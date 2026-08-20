from rest_framework.views import exception_handler as drf_exception_handler


def custom_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is None:
        return None

    codes = exc.get_codes()

    if isinstance(codes, dict):
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
    return response
