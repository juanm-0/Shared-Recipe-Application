from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import exceptions
from rest_framework.views import exception_handler as drf_exception_handler


def custom_exception_handler(exc, context):
    if isinstance(exc, DjangoValidationError):
        detail = exc.message_dict if hasattr(exc, "message_dict") else exc.messages
        exc = exceptions.ValidationError(detail=detail)

    response = drf_exception_handler(exc, context)
    if response is None:
        return None

    if isinstance(exc, Http404):
        exc = exceptions.NotFound(*exc.args)
    elif isinstance(exc, DjangoPermissionDenied):
        exc = exceptions.PermissionDenied(*exc.args)

    codes = exc.get_codes()

    if isinstance(exc, exceptions.ValidationError):
        response.data = {
            "detail": "Validation failed.",
            "code": "validation_error",
            "errors": response.data,
        }
    elif isinstance(response.data, dict) and "detail" in response.data:
        response.data = {
            "detail": str(response.data["detail"]),
            "code": codes,
        }
    else:
        response.data = {
            "detail": str(response.data),
            "code": codes,
        }

    extra_context = getattr(exc, "extra_context", None)
    if extra_context:
        response.data.update(extra_context)

    return response
