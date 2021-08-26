""" constants for videos """
from main.constants import STATUS_COMPLETE, STATUS_CREATED, STATUS_FAILED


DESTINATION_YOUTUBE = "youtube"
DESTINATION_ARCHIVE = "archive"

ALL_DESTINATIONS = [DESTINATION_YOUTUBE, DESTINATION_ARCHIVE]


class VideoStatus:
    """Simple class for possible VideoFile statuses"""

    CREATED = STATUS_CREATED
    TRANSCODING = "Transcoding"
    FAILED = STATUS_FAILED
    COMPLETE = STATUS_COMPLETE

    ALL_STATUSES = [CREATED, TRANSCODING, FAILED, COMPLETE]


class VideoJobStatus:
    """Simple class for possible VideoJob statuses"""

    CREATED = STATUS_CREATED
    FAILED = STATUS_FAILED
    COMPLETE = STATUS_COMPLETE


class VideoFileStatus:
    """Simple class for possible VideoFile statuses"""

    CREATED = STATUS_CREATED
    UPLOADED = "Uploaded"
    FAILED = STATUS_FAILED
    COMPLETE = STATUS_COMPLETE