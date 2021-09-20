""" Tests for websites.serializers """
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models import CharField, Value

from main.constants import ISO_8601_FORMAT
from users.factories import UserFactory
from users.models import User
from websites.constants import (
    CONTENT_TYPE_RESOURCE,
    ROLE_EDITOR,
    WEBSITE_SOURCE_OCW_IMPORT,
)
from websites.factories import (
    WebsiteCollectionFactory,
    WebsiteCollectionItemFactory,
    WebsiteContentFactory,
    WebsiteFactory,
    WebsiteStarterFactory,
)
from websites.models import WebsiteCollectionItem, WebsiteContent, WebsiteStarter
from websites.serializers import (
    WebsiteCollaboratorSerializer,
    WebsiteCollectionItemSerializer,
    WebsiteCollectionSerializer,
    WebsiteContentCreateSerializer,
    WebsiteContentDetailSerializer,
    WebsiteContentSerializer,
    WebsiteDetailSerializer,
    WebsiteSerializer,
    WebsiteStarterDetailSerializer,
    WebsiteStarterSerializer,
)


pytestmark = pytest.mark.django_db


def test_serialize_website_course():
    """
    Verify that a serialized website contains expected fields
    """
    site = WebsiteFactory.create()
    serialized_data = WebsiteSerializer(instance=site).data
    assert serialized_data["name"] == site.name
    assert serialized_data["short_id"] == site.short_id
    assert serialized_data["publish_date"] == site.publish_date.strftime(
        ISO_8601_FORMAT
    )
    assert serialized_data["metadata"] == site.metadata
    assert isinstance(serialized_data["starter"], dict)
    assert (
        serialized_data["starter"]
        == WebsiteStarterSerializer(instance=site.starter).data
    )


def test_website_starter_serializer():
    """WebsiteStarterSerializer should serialize a WebsiteStarter object with the correct fields"""
    starter = WebsiteStarterFactory.build()
    serialized_data = WebsiteStarterSerializer(instance=starter).data
    assert serialized_data["name"] == starter.name
    assert serialized_data["path"] == starter.path
    assert serialized_data["source"] == starter.source
    assert serialized_data["commit"] == starter.commit
    assert "config" not in serialized_data


def test_website_starter_detail_serializer():
    """WebsiteStarterDetailSerializer should serialize a WebsiteStarter object with the correct fields"""
    starter = WebsiteStarterFactory.build()
    serialized_data = WebsiteStarterDetailSerializer(instance=starter).data
    assert serialized_data["name"] == starter.name
    assert serialized_data["path"] == starter.path
    assert serialized_data["source"] == starter.source
    assert serialized_data["commit"] == starter.commit
    assert "config" in serialized_data
    assert isinstance(serialized_data["config"], dict)


def test_website_detail_deserialize():
    """WebsiteSerializer should deserialize website data"""
    serializer = WebsiteDetailSerializer(
        data={
            "name": "my-site",
            "title": "My Title",
            "short_id": "my-title",
            "source": WEBSITE_SOURCE_OCW_IMPORT,
            "metadata": None,
            "starter": 1,
        }
    )
    assert serializer.is_valid()


@pytest.mark.parametrize("has_starter", [True, False])
def test_website_serializer(has_starter):
    """WebsiteSerializer should serialize a Website object with the correct fields"""
    website = (
        WebsiteFactory.build() if has_starter else WebsiteFactory.build(starter=None)
    )
    serialized_data = WebsiteSerializer(instance=website).data
    assert serialized_data["name"] == website.name
    assert serialized_data["title"] == website.title
    assert serialized_data["metadata"] == website.metadata
    assert "config" not in serialized_data


@pytest.mark.parametrize("has_starter", [True, False])
def test_website_detail_serializer(has_starter):
    """WebsiteDetailSerializer should serialize a Website object with the correct fields, including config"""
    website = (
        WebsiteFactory.build() if has_starter else WebsiteFactory.build(starter=None)
    )
    serialized_data = WebsiteDetailSerializer(instance=website).data
    assert serialized_data["name"] == website.name
    assert serialized_data["title"] == website.title
    assert serialized_data["metadata"] == website.metadata
    assert serialized_data["starter"] == (
        WebsiteStarterDetailSerializer(instance=website.starter).data
        if has_starter
        else None
    )


def test_website_collaborator_serializer():
    """ WebsiteCollaboratorSerializer should serialize a User object with correct fields """
    collaborator = (
        User.objects.filter(id=UserFactory.create().id)
        .annotate(role=Value(ROLE_EDITOR, CharField()))
        .first()
    )
    serialized_data = WebsiteCollaboratorSerializer(instance=collaborator).data
    assert serialized_data["user_id"] == collaborator.id
    assert serialized_data["name"] == collaborator.name
    assert serialized_data["email"] == collaborator.email
    assert serialized_data["role"] == ROLE_EDITOR


def test_website_content_serializer():
    """WebsiteContentSerializer should serialize a few fields to identify the content"""
    content = WebsiteContentFactory.create()
    serialized_data = WebsiteContentSerializer(instance=content).data
    assert serialized_data["text_id"] == str(content.text_id)
    assert serialized_data["title"] == content.title
    assert serialized_data["type"] == content.type
    assert "markdown" not in serialized_data
    assert "metadata" not in serialized_data


def test_website_content_detail_serializer():
    """WebsiteContentDetailSerializer should serialize all relevant fields to the frontend"""
    content = WebsiteContentFactory.create()
    serialized_data = WebsiteContentDetailSerializer(instance=content).data
    assert serialized_data["text_id"] == str(content.text_id)
    assert serialized_data["title"] == content.title
    assert serialized_data["type"] == content.type
    assert serialized_data["markdown"] == content.markdown
    assert serialized_data["metadata"] == content.metadata


@pytest.mark.parametrize("is_resource", [True, False])
def test_website_content_detail_serializer_youtube_ocw(settings, is_resource):
    """WebsiteContent serializers should conditionally fill in youtube thumbnail metadata"""
    settings.OCW_IMPORT_STARTER_SLUG = "course"
    starter = WebsiteStarter.objects.get(slug=settings.OCW_IMPORT_STARTER_SLUG)
    website = WebsiteFactory.create(starter=starter)
    youtube_id = "abc123"
    content_type = "resource" if is_resource else "page"
    existing_content = WebsiteContentFactory.create(
        type=content_type,
        website=website,
    )
    data = (
        {
            "metadata": {
                "video_metadata": {"youtube_id": youtube_id},
                "video_files": {"video_thumbnail_file": ""},
            },
        }
        if is_resource
        else {"metadata": {"body": "text"}}
    )
    existing_serializer = WebsiteContentDetailSerializer()
    existing_serializer.update(existing_content, data)

    data["type"] = content_type
    data["title"] = "new content"
    new_serializer = WebsiteContentCreateSerializer()
    new_serializer.context["website_id"] = website.uuid
    new_content = new_serializer.create(data)

    for content in [existing_content, new_content]:
        if is_resource:
            assert content.metadata["video_metadata"]["youtube_id"] == youtube_id
            assert (
                content.metadata["video_files"]["video_thumbnail_file"]
                == f"https://img.youtube.com/vi/{youtube_id}/0.jpg"
            )
        else:
            assert content.metadata["body"] == "text"


def test_website_content_detail_with_file_serializer():
    """WebsiteContentDetailSerializer should include its file url in metadata"""
    content = WebsiteContentFactory.create(type="resource", metadata={"title": "Test"})
    content.file = SimpleUploadedFile("test.txt", b"content")

    serialized_data = WebsiteContentDetailSerializer(instance=content).data
    assert serialized_data["image"] == content.file.url
    assert serialized_data["metadata"]["title"] == content.metadata["title"]


@pytest.mark.parametrize("content_context", [True, False])
@pytest.mark.parametrize("multiple", [True, False])
@pytest.mark.parametrize("invalid_data", [True, False])
@pytest.mark.parametrize("nested", [True, False])
@pytest.mark.parametrize("field_order_reversed", [True, False])
def test_website_content_detail_serializer_content_context(
    content_context, multiple, invalid_data, nested, field_order_reversed
):
    """WebsiteContentDetailSerializer should serialize content_context for relation and menu fields"""
    relation_field = {
        "name": "relation_field_name",
        "label": "Relation field label",
        "multiple": multiple,
        "widget": "relation",
    }
    menu_field = {
        "name": "menu_field_name",
        "label": "Menu field label",
        "widget": "menu",
    }
    field_list = [menu_field, relation_field]
    if field_order_reversed:
        field_list = list(reversed(field_list))
    website = WebsiteFactory.create(
        starter__config={
            "collections": [
                {
                    "fields": [{"name": "outer", "fields": field_list}]
                    if nested
                    else field_list
                }
            ]
        }
    )
    menu_referenced = WebsiteContentFactory.create(website=website)
    relation_referenced = WebsiteContentFactory.create()
    referenced_list = [menu_referenced, relation_referenced]
    if field_order_reversed:
        referenced_list = list(reversed(referenced_list))
    for content in referenced_list:
        # These have the same text_id but a different website so it should not match and therefore be ignored
        WebsiteContentFactory.create(text_id=content.text_id)
    metadata = {
        relation_field["name"]: {
            "content": [relation_referenced.text_id]
            if multiple
            else relation_referenced.text_id,
            "website": relation_referenced.website.name,
        },
        menu_field["name"]: [
            {
                "identifier": "external-not-a-match",
            },
            {"identifier": "uuid-not-found-so-ignored"},
            {
                "identifier": menu_referenced.text_id,
            },
        ],
    }
    if invalid_data:
        metadata = {}
    elif nested:
        metadata = {"outer": metadata}

    content = WebsiteContentFactory.create(website=website, metadata=metadata)
    serialized_data = WebsiteContentDetailSerializer(
        instance=content, context={"content_context": content_context}
    ).data
    assert serialized_data["text_id"] == str(content.text_id)
    assert serialized_data["title"] == content.title
    assert serialized_data["type"] == content.type
    assert serialized_data["markdown"] == content.markdown
    assert serialized_data["metadata"] == content.metadata
    assert serialized_data["content_context"] == (
        (
            []
            if invalid_data
            else WebsiteContentDetailSerializer(
                instance=referenced_list, many=True, context={"content_context": False}
            ).data
        )
        if content_context
        else None
    )


def test_website_content_detail_serializer_save(mocker):
    """WebsiteContentDetailSerializer should modify only certain fields"""
    mock_update_website_backend = mocker.patch(
        "websites.serializers.update_website_backend"
    )
    mock_create_website_pipeline = mocker.patch(
        "websites.serializers.create_website_publishing_pipeline"
    )
    content = WebsiteContentFactory.create(type=CONTENT_TYPE_RESOURCE)
    existing_text_id = content.text_id
    new_title = f"{content.title} with some more text"
    new_type = f"{content.type}_other"
    new_markdown = "hopefully different from the previous markdown"
    metadata = {"description": "data"}
    user = UserFactory.create()
    # uuid value is invalid but it's ignored since it's marked readonly
    serializer = WebsiteContentDetailSerializer(
        data={
            "title": new_title,
            "text_id": "----",
            "type": new_type,
            "markdown": new_markdown,
            "metadata": metadata,
        },
        instance=content,
        context={
            "view": mocker.Mock(kwargs={"parent_lookup_website": content.website.name}),
            "request": mocker.Mock(user=user),
        },
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    content.refresh_from_db()
    assert content.title == new_title
    assert content.text_id == existing_text_id
    assert content.type != new_type
    assert content.markdown == new_markdown
    assert content.metadata == metadata
    assert content.updated_by == user
    mock_update_website_backend.assert_called_once_with(content.website)
    mock_create_website_pipeline.assert_not_called()


@pytest.mark.parametrize("add_context_data", [True, False])
def test_website_content_create_serializer(mocker, add_context_data):
    """
    WebsiteContentCreateSerializer should create a new WebsiteContent object, using context data as an override
    if extra context data is passed in.
    """
    mock_update_website_backend = mocker.patch(
        "websites.serializers.update_website_backend"
    )
    website = WebsiteFactory.create()
    user = UserFactory.create()
    metadata = {"description": "some text"}
    payload = {
        "website_id": website.pk,
        "text_id": "my-text-id",
        "title": "a title",
        "type": CONTENT_TYPE_RESOURCE,
        "markdown": "some markdown",
        "metadata": metadata,
        "is_page_content": False,
        "dirpath": "path/to",
        "filename": "myfile",
    }
    override_context_data = (
        {}
        if not add_context_data
        else {
            "is_page_content": True,
            "dirpath": "override/path",
            "filename": "overridden-filename",
        }
    )
    context = {
        "view": mocker.Mock(kwargs={"parent_lookup_website": website.name}),
        "request": mocker.Mock(user=user),
        "website_id": website.pk,
        **override_context_data,
    }
    serializer = WebsiteContentCreateSerializer(data=payload, context=context)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    content = WebsiteContent.objects.get(title=payload["title"])
    mock_update_website_backend.assert_called_once_with(content.website)
    assert content.website_id == website.pk
    assert content.owner == user
    assert content.updated_by == user
    assert content.title == payload["title"]
    assert content.text_id == payload["text_id"]
    assert content.markdown == payload["markdown"]
    assert content.type == payload["type"]
    assert content.metadata == metadata
    assert content.is_page_content is (
        False if not add_context_data else override_context_data["is_page_content"]
    )
    assert content.dirpath == (
        "path/to" if not add_context_data else override_context_data["dirpath"]
    )
    assert content.filename == (
        "myfile" if not add_context_data else override_context_data["filename"]
    )


def test_website_collection_serializer():
    """
    test that the fields we want come through
    """
    website_collection = WebsiteCollectionFactory.create()
    WebsiteCollectionItemFactory.create(website_collection=website_collection)
    WebsiteCollectionItemFactory.create(website_collection=website_collection)
    WebsiteCollectionItemFactory.create(website_collection=website_collection)
    serialized_data = WebsiteCollectionSerializer(instance=website_collection).data
    assert serialized_data["title"] == website_collection.title
    assert serialized_data["description"] == website_collection.description
    assert serialized_data["id"] == website_collection.id


def test_website_collection_item_serializer():
    """
    simple test to check that fields come through
    """
    item = WebsiteCollectionItemFactory.create()
    serialized_data = WebsiteCollectionItemSerializer(instance=item).data
    assert serialized_data["position"] == item.position
    assert serialized_data["website_collection"] == item.website_collection.id
    assert serialized_data["website"] == item.website.uuid
    assert serialized_data["id"] == item.id
    assert serialized_data["website_title"] == item.website.title


def test_website_collection_item_create():
    """
    test that the position value is incremented correctly when creating a new item
    """
    website_collection = WebsiteCollectionFactory.create()
    WebsiteCollectionItemFactory.create(
        website_collection=website_collection, position=0
    )
    WebsiteCollectionItemFactory.create(
        website_collection=website_collection, position=1
    )
    WebsiteCollectionItemFactory.create(
        website_collection=website_collection, position=2
    )
    website = WebsiteFactory.create()

    payload = {"website": website.uuid}
    serializer = WebsiteCollectionItemSerializer(
        data=payload,
        context={
            "website_collection_id": website_collection.id,
        },
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    item = WebsiteCollectionItem.objects.get(
        website_collection=website_collection, website=website
    )
    assert item.position == 3


def test_website_collection_item_update():
    """
    test moving items up and down the list
    """
    website_collection = WebsiteCollectionFactory.create()
    one = WebsiteCollectionItemFactory.create(
        website_collection=website_collection, position=0
    )
    two = WebsiteCollectionItemFactory.create(
        website_collection=website_collection, position=1
    )
    three = WebsiteCollectionItemFactory.create(
        website_collection=website_collection, position=2
    )
    four = WebsiteCollectionItemFactory.create(
        website_collection=website_collection, position=3
    )
    five = WebsiteCollectionItemFactory.create(
        website_collection=website_collection, position=4
    )
    six = WebsiteCollectionItemFactory.create(
        website_collection=website_collection, position=5
    )

    # test moving item up the list
    serializer = WebsiteCollectionItemSerializer(
        data={
            "position": 1,
            "website": five.website.uuid,
        },
        instance=five,
        context={"website_collection_id": website_collection.id},
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()

    assert list(
        WebsiteCollectionItem.objects.filter(
            website_collection=website_collection
        ).order_by("position")
    ) == [one, five, two, three, four, six]

    # move item back down the list
    serializer = WebsiteCollectionItemSerializer(
        data={
            "position": 4,
            "website": five.website.uuid,
        },
        instance=five,
        context={"website_collection_id": website_collection.id},
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()

    assert list(
        WebsiteCollectionItem.objects.filter(
            website_collection=website_collection
        ).order_by("position")
    ) == [one, two, three, four, five, six]
