import json
from http import HTTPStatus
from django.http import JsonResponse


## ~~ JSON RESPONSES


class JsonResponseNotFound(JsonResponse):
    def __init__(self, message="object not found"):
        self.status_code = HTTPStatus.NOT_FOUND
        super().__init__(
            {
                "success": False,
                "message": message,
            }
        )


class JsonResponseUnauthorized(JsonResponse):
    def __init__(self, message="unauthorized"):
        self.status_code = HTTPStatus.NOT_FOUND
        super().__init__(
            {
                "success": False,
                "message": message,
            }
        )


class JsonResponseBadRequest(JsonResponse):
    def __init__(self, message="bad request"):
        self.status_code = HTTPStatus.NOT_FOUND
        super().__init__(
            {
                "success": False,
                "message": message,
            }
        )


class JsonResponseFail(JsonResponse):
    def __init__(self, message="fail", payload={}):
        super().__init__(
            {
                "success": False,
                "message": message,
                "payload": payload,
            }
        )


class JsonResponseSuccess(JsonResponse):
    def __init__(self, message="ok", payload={}):
        super().__init__(
            {
                "success": True,
                "message": message,
                "payload": payload,
            }
        )


## ~~ DECORATORS


def validate_post_request(operations: list):
    """Decorator ensures the following about the post request:
    1. it has a body
    2. the body has a valid operation."""

    def decorator(func):
        def wrapper(request, *args, **kwargs):
            if not request.body:
                return JsonResponseBadRequest()
            body = json.loads(request.body)
            operation = body.get("operation")
            if operation not in operations:
                return JsonResponseBadRequest(f"invalid operation: {operation}")
            return func(request, *args, **kwargs)

        return wrapper

    return decorator
