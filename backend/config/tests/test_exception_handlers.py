from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.http import Http404
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


def test_http404_reshaped_to_not_found():
    response = custom_exception_handler(Http404(), {})
    assert response.status_code == 404
    assert response.data["code"] == "not_found"


def test_django_permission_denied_reshaped():
    response = custom_exception_handler(DjangoPermissionDenied(), {})
    assert response.status_code == 403
    assert response.data["code"] == "permission_denied"


from rest_framework.exceptions import APIException


def test_extra_context_is_merged_into_response_body():
    class _WithContext(APIException):
        status_code = 409
        default_detail = "Conflict."
        default_code = "test_conflict"

        def __init__(self):
            super().__init__()
            self.extra_context = {"current": {"id": 1}}

    response = custom_exception_handler(_WithContext(), {})
    assert response.status_code == 409
    assert response.data["code"] == "test_conflict"
    assert response.data["current"] == {"id": 1}


def test_exception_without_extra_context_is_unaffected():
    response = custom_exception_handler(NotAuthenticated(), {})
    assert "current" not in response.data
