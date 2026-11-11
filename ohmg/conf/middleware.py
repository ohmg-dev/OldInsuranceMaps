from fnmatch import fnmatch

from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.middleware import csrf
from django.urls import reverse

from ohmg.api.schemas import UserSchema
from ohmg.conf.http import on_mobile


class LoginRequiredMiddleware:
    """
    Based on: https://stackoverflow.com/a/2164224/3873885,
    see link for fuller implementation.

    Middleware component that wraps the login_required decorator around
    matching URL patterns. To use, add the class to MIDDLEWARE_CLASSES and
    define LOGIN_REQUIRED_URLS and LOGIN_REQUIRED_URLS_EXCEPTIONS in your
    settings.py. For example:
    ------
    LOGIN_REQUIRED_URLS = (
        r'/topsecret/(.*)$',
    )
    LOGIN_REQUIRED_URLS_EXCEPTIONS = (
        r'/topsecret/login(.*)$',
        r'/topsecret/logout(.*)$',
    )
    ------
    LOGIN_REQUIRED_URLS is where you define URL patterns; each pattern must
    be a valid regex.

    LOGIN_REQUIRED_URLS_EXCEPTIONS is, conversely, where you explicitly
    define any exceptions (like login and logout URLs).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # No need to process URLs if user already logged in
        if request.user.is_authenticated:
            return self.get_response(request)

        if request.path == settings.LOGIN_URL:
            return self.get_response(request)

        else:
            return redirect_to_login(request.get_full_path())


class CORSMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if any([fnmatch(request.path, i) for i in settings.CORS_WHITELIST]):
            response["Access-Control-Allow-Origin"] = "*"

        return response


class OHMGContextMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            user = request.user
        except AttributeError:
            user = None
        if user and user.is_authenticated:
            user_info = UserSchema.from_orm(user).dict()
            user_info["api_keys"] = user.api_keys
            user_info["is_authenticated"] = True
            user_info["is_staff"] = user.is_staff
            user_info["perms"] = sorted(list(user.get_all_permissions()))
            user_info["loaded_maps"] = list(user.maps.values_list("pk", flat=True))
        else:
            user_info = {
                "is_authenticated": False,
                "is_staff": False,
                "perms": [],
                "loaded_maps": [],
            }

        request.ohmg_context = {
            "site_url": settings.SITEURL,
            "titiler_host": settings.TITILER_HOST,
            "mapbox_api_token": settings.MAPBOX_API_TOKEN,
            "csrf_token": (csrf_token := csrf.get_token(request)),
            "session_length": settings.GEOREFERENCE_SESSION_LENGTH,
            "on_mobile": on_mobile(request)["on_mobile"],
            "user": user_info,
            "change_avatar_url": reverse("avatar_change"),
            "ohmg_api_headers": {
                "X-API-Key": settings.OHMG_API_KEY,
            },
            "ohmg_post_headers": {
                "Content-Type": "application/json;charset=utf-8",
                "X-CSRFToken": csrf_token,
            },
            "max_tiles_loading": settings.OPENLAYERS_MAX_TILES_LOADING,
            "path": request.path,
        }

        response = self.get_response(request)
        return response
