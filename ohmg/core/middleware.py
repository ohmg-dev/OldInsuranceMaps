from django.conf import settings
from django.contrib.auth.views import redirect_to_login


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

        for path in settings.CORS_WHITELIST:
            if request.path.startswith(path):
                response["Access-Control-Allow-Origin"] = "*"

        return response
