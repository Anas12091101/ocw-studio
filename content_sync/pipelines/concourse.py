""" Concourse-CI preview/publish pipeline generator"""
import json
import logging
import os
from typing import Dict, Tuple
from urllib.parse import quote, urljoin, urlparse

import requests
import yaml
from concoursepy.api import Api as BaseConcourseApi
from django.conf import settings
from requests import HTTPError

from content_sync.decorators import retry_on_failure
from content_sync.pipelines.base import BaseSyncPipeline
from websites.constants import (
    PUBLISH_STATUS_NOT_STARTED,
    PUBLISH_STATUS_PENDING,
    STARTER_SOURCE_GITHUB,
)
from websites.models import Website
from websites.site_config_api import SiteConfig


log = logging.getLogger(__name__)


class ConcourseApi(BaseConcourseApi):
    """
    Customized version of concoursepy.api.Api that allows for getting/setting headers
    """

    def get_with_headers(
        self, path: str, stream: bool = False, iterator: bool = False
    ) -> Tuple[Dict, Dict]:
        """Customized base get method, returning response data and headers"""
        url = self._make_api_url(path)
        r = self.requests.get(url, headers=self.headers, stream=stream)
        if not self._is_response_ok(r) and self.has_username_and_passwd:
            self.auth()
            r = self.requests.get(url, headers=self.headers, stream=stream)
        if r.status_code == requests.codes.ok:
            if stream:
                if iterator:
                    response_data = self.iter_sse_stream(r)
                else:
                    response_data = list(self.iter_sse_stream(r))
            else:
                response_data = json.loads(r.text)
            return response_data, r.headers
        else:
            r.raise_for_status()

    @retry_on_failure
    def put_with_headers(
        self, path: str, data: Dict = None, headers: Dict = None
    ) -> bool:
        """
        Allow additional headers to be sent with a put request
        """
        url = self._make_api_url(path)
        request_headers = self.headers
        request_headers.update(headers or {})
        kwargs = {"headers": request_headers}
        if data is not None:
            kwargs["data"] = data
        r = self.requests.put(url, **kwargs)
        if not self._is_response_ok(r) and self.has_username_and_passwd:
            self.auth()
            r = self.requests.put(url, **kwargs)
        if r.status_code == requests.codes.ok:
            return True
        else:
            r.raise_for_status()
        return False

    @retry_on_failure
    def post(self, path, data=None):
        """Same as base post method but with a retry"""
        super().post(path, data)

    @retry_on_failure
    def put(self, path, data=None):
        """Same as base put method but with a retry"""
        super().put(path, data)


class ConcourseGithubPipeline(BaseSyncPipeline):
    """
    Concourse-CI publishing pipeline, dependent on a Github backend
    """

    MANDATORY_SETTINGS = [
        "AWS_PREVIEW_BUCKET_NAME",
        "AWS_PUBLISH_BUCKET_NAME",
        "AWS_STORAGE_BUCKET_NAME",
        "CONCOURSE_URL",
        "CONCOURSE_USERNAME",
        "CONCOURSE_PASSWORD",
        "GIT_BRANCH_PREVIEW",
        "GIT_BRANCH_RELEASE",
        "GIT_DOMAIN",
        "GIT_ORGANIZATION",
        "GITHUB_WEBHOOK_BRANCH",
    ]

    def __init__(self, website: Website):
        """Initialize the pipeline API instance"""
        super().__init__(website)
        self.instance_vars = quote(json.dumps({"site": self.website.name}))
        self.ci = ConcourseApi(
            settings.CONCOURSE_URL,
            settings.CONCOURSE_USERNAME,
            settings.CONCOURSE_PASSWORD,
            settings.CONCOURSE_TEAM,
        )

    def _make_builds_url(self, version: str, job_name: str):
        """Make URL for fetching builds information"""
        return f"/api/v1/teams/{settings.CONCOURSE_TEAM}/pipelines/{version}/jobs/{job_name}/builds?vars={self.instance_vars}"

    def _make_pipeline_config_url(self, version: str):
        """Make URL for fetching pipeline info"""
        return f"/api/v1/teams/{settings.CONCOURSE_TEAM}/pipelines/{version}/config?vars={self.instance_vars}"

    def _make_job_url(self, version: str, job_name: str):
        """Make URL for fetching job info"""
        return f"/api/v1/teams/{settings.CONCOURSE_TEAM}/pipelines/{version}/jobs/{job_name}?vars={self.instance_vars}"

    def _make_pipeline_unpause_url(self, version: str):
        """Make URL for unpausing a pipeline"""
        return f"/api/v1/teams/{settings.CONCOURSE_TEAM}/pipelines/{version}/unpause?vars={self.instance_vars}"

    def upsert_website_pipeline(self):  # pylint:disable=too-many-locals
        """
        Create or update a concourse pipeline for the given Website
        """
        starter = self.website.starter
        if starter.source != STARTER_SOURCE_GITHUB:
            # This pipeline only handles sites with github-based starters
            return
        starter_path_url = urlparse(starter.path)
        if not starter_path_url.netloc:
            # Invalid github url, so skip
            return

        site_config = SiteConfig(self.website.starter.config)
        site_url = f"{site_config.root_url_path}/{self.website.name}".strip("/")
        base_url = "" if self.website.name == settings.ROOT_WEBSITE_NAME else site_url
        purge_header = (
            ""
            if settings.CONCOURSE_HARD_PURGE
            else "\n              - -H\n              - 'Fastly-Soft-Purge: 1'"
        )
        hugo_projects_url = urljoin(
            f"{starter_path_url.scheme}://{starter_path_url.netloc}",
            f"{'/'.join(starter_path_url.path.strip('/').split('/')[:2])}.git",  # /<org>/<repo>.git
        )

        for branch in [settings.GIT_BRANCH_PREVIEW, settings.GIT_BRANCH_RELEASE]:
            if branch == settings.GIT_BRANCH_PREVIEW:
                version = self.VERSION_DRAFT
                destination_bucket = settings.AWS_PREVIEW_BUCKET_NAME
                static_api_url = settings.OCW_STUDIO_DRAFT_URL
            else:
                version = self.VERSION_LIVE
                destination_bucket = settings.AWS_PUBLISH_BUCKET_NAME
                static_api_url = settings.OCW_STUDIO_LIVE_URL
            with open(
                os.path.join(
                    os.path.dirname(__file__), "definitions/concourse/site-pipeline.yml"
                )
            ) as pipeline_config_file:
                config_str = (
                    pipeline_config_file.read()
                    .replace("((git-domain))", settings.GIT_DOMAIN)
                    .replace("((github-org))", settings.GIT_ORGANIZATION)
                    .replace("((ocw-bucket))", destination_bucket)
                    .replace(
                        "((ocw-hugo-projects-branch))", settings.GITHUB_WEBHOOK_BRANCH
                    )
                    .replace("((ocw-hugo-projects-uri))", hugo_projects_url)
                    .replace("((ocw-studio-url))", settings.SITE_BASE_URL)
                    .replace("((static-api-base-url))", static_api_url)
                    .replace(
                        "((ocw-import-starter-slug))", settings.OCW_IMPORT_STARTER_SLUG
                    )
                    .replace("((ocw-studio-bucket))", settings.AWS_STORAGE_BUCKET_NAME)
                    .replace("((ocw-site-repo))", self.website.short_id)
                    .replace("((ocw-site-repo-branch))", branch)
                    .replace("((config-slug))", self.website.starter.slug)
                    .replace("((base-url))", base_url)
                    .replace("((site-url))", site_url)
                    .replace("((site-name))", self.website.name)
                    .replace("((purge-url))", f"purge/{self.website.name}")
                    .replace("((purge_header))", purge_header)
                    .replace("((version))", version)
                )
            config = json.dumps(yaml.load(config_str, Loader=yaml.SafeLoader))
            log.debug(config)
            # Try to get the version of the pipeline if it already exists, because it will be
            # necessary to update an existing pipeline.
            url_path = self._make_pipeline_config_url(version)
            try:
                _, headers = self.ci.get_with_headers(url_path)
                version_headers = {
                    "X-Concourse-Config-Version": headers["X-Concourse-Config-Version"]
                }
            except HTTPError:
                version_headers = None
            self.ci.put_with_headers(url_path, data=config, headers=version_headers)

    def trigger_pipeline_build(self, version: str):
        """Trigger a pipeline build"""
        pipeline_info = self.ci.get(self._make_pipeline_config_url(version))
        job_name = pipeline_info["config"]["jobs"][0]["name"]
        self.ci.post(self._make_builds_url(version, job_name))

    def unpause_pipeline(self, version):
        """Unpause the pipeline"""
        self.ci.put(self._make_pipeline_unpause_url(version))

    def get_latest_build_status(self, version):
        """
        Get the status of a build for a site

        Args:
            version (str): Either draft or live

        Returns:
            str:
                The status of the currently running or most recently finished build.
                status is one of websites.constants.PUBLISH_STATUSES
        """
        pipeline_info = self.ci.get(self._make_pipeline_config_url(version))
        job_name = pipeline_info["config"]["jobs"][0]["name"]
        try:
            job_info = self.ci.get(self._make_job_url(version, job_name))
        except requests.exceptions.HTTPError as ex:
            if ex.response.status_code == 404:
                return PUBLISH_STATUS_NOT_STARTED
            else:
                raise

        if (
            job_info.get("next_build")
            and job_info["next_build"].get("status") == PUBLISH_STATUS_PENDING
        ):
            return PUBLISH_STATUS_PENDING

        if job_info.get("finished_build"):
            return job_info["finished_build"].get("status", PUBLISH_STATUS_NOT_STARTED)
        return PUBLISH_STATUS_NOT_STARTED
