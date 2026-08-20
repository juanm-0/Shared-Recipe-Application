from rest_framework.exceptions import NotAuthenticated, ValidationError

from config.exception_handlers import custom_exception_handler


def test_simple_exception_reshaped_to_detail_and_code():
    exc = NotAuthenticated()
    response = custom_exception_handler(exc, {})
    assert response.status_code == 401
    assert response.data == {
        "detail": "Authentication credentials were not provided.",
        "code": "not_authenticated",
    }


def test_validation_error_with_field_errors_reshaped():
    exc = ValidationError({"username": ["This field is required."]})
    response = custom_exception_handler(exc, {})
    assert response.status_code == 400
    assert response.data["code"] == "validation_error"
    assert response.data["detail"] == "Validation failed."
    assert response.data["errors"] == {"username": ["This field is required."]}


def test_non_api_exception_returns_none():
    exc = ValueError("boom")
    response = custom_exception_handler(exc, {})
    assert response is None
