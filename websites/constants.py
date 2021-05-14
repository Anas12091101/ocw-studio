""" Constants for websites """

CONTENT_TYPE_PAGE = "page"
CONTENT_TYPE_RESOURCE = "resource"

COURSE_HOME = "course-home"
COURSE_PAGE_LAYOUTS = ["course_home", "course_section", "instructor_insights"]
COURSE_RESOURCE_LAYOUTS = ["pdf", "video"]

CONTENT_FILENAME_MAX_LEN = 125
CONTENT_DIRPATH_MAX_LEN = 300
CONTENT_FILEPATH_UNIQUE_CONSTRAINT = "unique_page_content_destination"

WEBSITE_SOURCE_STUDIO = "studio"
WEBSITE_SOURCE_OCW_IMPORT = "ocw-import"
WEBSITE_SOURCES = [WEBSITE_SOURCE_STUDIO, WEBSITE_SOURCE_OCW_IMPORT]

STARTER_SOURCE_GITHUB = "github"
STARTER_SOURCE_LOCAL = "local"
STARTER_SOURCES = [STARTER_SOURCE_GITHUB, STARTER_SOURCE_LOCAL]

WEBSITE_CONFIG_FILENAME = "ocw-studio.yml"
WEBSITE_CONFIG_CONTENT_DIR_KEY = "content-dir"
WEBSITE_CONFIG_DEFAULT_CONTENT_DIR = "content"
WEBSITE_CONTENT_FILETYPE = "md"

COURSE_STARTER_SLUG = "course"


GLOBAL_ADMIN = "global_admin"
GLOBAL_AUTHOR = "global_author"

ADMIN_GROUP_PREFIX = "admins_website_"
EDITOR_GROUP_PREFIX = "editors_website_"


PERMISSION_ADD = "websites.add_website"
PERMISSION_VIEW = "websites.view_website"
PERMISSION_PREVIEW = "websites.preview_website"
PERMISSION_EDIT = "websites.change_website"
PERMISSION_PUBLISH = "websites.publish_website"
PERMISSION_EDIT_CONTENT = "websites.edit_content_website"
PERMISSION_COLLABORATE = "websites.add_collaborators_website"

ROLE_ADMINISTRATOR = "admin"
ROLE_EDITOR = "editor"
ROLE_GLOBAL = "global_admin"
ROLE_OWNER = "owner"

GROUP_ROLES = {ROLE_ADMINISTRATOR, ROLE_EDITOR}
ROLE_GROUP_MAPPING = {
    ROLE_ADMINISTRATOR: ADMIN_GROUP_PREFIX,
    ROLE_EDITOR: EDITOR_GROUP_PREFIX,
    ROLE_GLOBAL: GLOBAL_ADMIN,
}

PERMISSIONS_GLOBAL_AUTHOR = [PERMISSION_ADD]
PERMISSIONS_EDITOR = [PERMISSION_VIEW, PERMISSION_PREVIEW, PERMISSION_EDIT_CONTENT]
PERMISSIONS_ADMIN = PERMISSIONS_EDITOR + [
    PERMISSION_PUBLISH,
    PERMISSION_COLLABORATE,
    PERMISSION_EDIT,
]
