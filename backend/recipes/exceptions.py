from rest_framework import status
from rest_framework.exceptions import APIException


class StaleWrite(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "This recipe has been modified since you last loaded it."
    default_code = "stale_write"

    def __init__(self, current_data):
        super().__init__()
        self.extra_context = {"current": current_data}


class TagLimitExceeded(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "tag_limit_exceeded"

    def __init__(self, count):
        super().__init__(detail=f"A recipe can have at most 5 tags (received {count}).")


class DuplicateReview(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_code = "duplicate_review"

    def __init__(self, review_id):
        super().__init__(detail="You have already reviewed this recipe.")
        self.extra_context = {"review_id": review_id}
