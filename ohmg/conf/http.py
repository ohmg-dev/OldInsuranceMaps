import json
import re
from http import HTTPStatus

from django.conf import settings
from django.http import JsonResponse
from django.middleware import csrf
from django.urls import reverse

from ohmg.api.schemas import UserSchema

## ~~ CONTEXT GENERATION


def on_mobile(request):
    """determine if user on mobile device or not"""
    MOBILE_AGENT_RE = re.compile(r".*(iphone|mobile|androidtouch)", re.IGNORECASE)

    on_mobile = False
    user_agent = request.META.get("HTTP_USER_AGENT")
    if user_agent and MOBILE_AGENT_RE.match(user_agent):
        on_mobile = True

    return {
        "on_mobile": on_mobile,
    }


def user_info_from_request(request):
    """Return a set of info for the current user in the request."""

    try:
        user = request.user
    except AttributeError:
        user = None
    if user and user.is_authenticated:
        user_info = UserSchema.from_orm(user).dict()
        user_info["api_keys"] = user.api_keys
        user_info["is_authenticated"] = True
        user_info["is_staff"] = user.is_staff
    else:
        user_info = {
            "is_authenticated": False,
            "is_staff": False,
        }
    return user_info


def generate_ohmg_context(request) -> dict:
    """Returns a dictionary containing context that is generally needed on most pages,
    providing a standard approach to passing context to Svelte components."""

    return {
        "site_url": settings.SITEURL,
        "titiler_host": settings.TITILER_HOST,
        "titiler_preview_host": settings.TITILER_PREVIEW_HOST,
        "mapbox_api_token": settings.MAPBOX_API_TOKEN,
        "csrf_token": (csrf_token := csrf.get_token(request)),
        "session_length": settings.GEOREFERENCE_SESSION_LENGTH,
        "on_mobile": on_mobile(request)["on_mobile"],
        "user": user_info_from_request(request),
        "change_avatar_url": reverse("avatar_change"),
        "ohmg_api_headers": {
            "X-API-Key": settings.OHMG_API_KEY,
        },
        "ohmg_post_headers": {
            "Content-Type": "application/json;charset=utf-8",
            "X-CSRFToken": csrf_token,
        },
        "max_tiles_loading": settings.OPENLAYERS_MAX_TILES_LOADING,
    }


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
