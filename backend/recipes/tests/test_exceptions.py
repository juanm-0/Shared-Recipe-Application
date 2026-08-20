from recipes.exceptions import StaleWrite, TagLimitExceeded, DuplicateReview
from config.exception_handlers import custom_exception_handler


def test_stale_write_carries_current_data_in_response():
    exc = StaleWrite(current_data={"id": 5, "name": "Soup"})
    response = custom_exception_handler(exc, {})
    assert response.status_code == 409
    assert response.data["code"] == "stale_write"
    assert response.data["current"] == {"id": 5, "name": "Soup"}


def test_tag_limit_exceeded_shape_and_message():
    exc = TagLimitExceeded(count=6)
    response = custom_exception_handler(exc, {})
    assert response.status_code == 400
    assert response.data["code"] == "tag_limit_exceeded"
    assert "6" in response.data["detail"]


def test_duplicate_review_carries_review_id_in_response():
    exc = DuplicateReview(review_id=42)
    response = custom_exception_handler(exc, {})
    assert response.status_code == 409
    assert response.data["code"] == "duplicate_review"
    assert response.data["review_id"] == 42
