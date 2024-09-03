import re
from django.conf import settings
from django.contrib.sites.models import Site
from django.middleware import csrf
from django.urls import reverse

from ohmg.core.schemas import UserSchema

def on_mobile(request):
    """ determine if user on mobile device or not """
    MOBILE_AGENT_RE=re.compile(r".*(iphone|mobile|androidtouch)",re.IGNORECASE)

    on_mobile = False
    user_agent = request.META.get('HTTP_USER_AGENT')
    if user_agent and MOBILE_AGENT_RE.match(user_agent):
        on_mobile = True

    return {
        "on_mobile": on_mobile,
    }

def user_info_from_request(request):
    """ Return a set of info for the current user in the request. """

    try:
        user = request.user
    except AttributeError:
        user = None
    if user and user.is_authenticated:
        user_info = UserSchema.from_orm(user).dict()
        user_info['is_authenticated'] = True
        user_info['is_staff'] = user.is_staff
    else:
        user_info = {
            'is_authenticated': False,
            'is_staff': False,
        }
    return user_info

def generate_ohmg_context(request):
    """ Returns a dictionary containing config information
    that is generally needed on most pages. It allows a more streamlined approach
    to passing this context to Svelte components. It should typically be called
    via views.py, rather than as an actual context processor. """

    internal_urls = {
        "get_annotation_set": reverse("api-beta:annotation_set"),
        "get_annotation_sets": reverse("api-beta:annotation_sets"),
        "post_annotation_set": reverse("annotation_set_view"),
        "get_places_geojson": reverse("api-beta:places_geojson"),
        "get_maps": reverse("api-beta:map_list"),
        "get_sessions": reverse("api-beta:session_list"),
        "get_sessions2": reverse("api-beta2:session_list"),
        "get_users": reverse("api-beta:user_list"),
        "get_place": reverse("api-beta2:place"),
        "get_places": reverse("api-beta2:place_list"),
        "change_avatar": reverse('avatar_change'),
    }

    csrf_token = csrf.get_token(request)
    return {
        "titiler_host": settings.TITILER_HOST,
        "mapbox_api_token": settings.MAPBOX_API_TOKEN,
        "ohmg_api_headers": {
            'X-API-Key': settings.OHMG_API_KEY,
        },
        "ohmg_post_headers": {
            'Content-Type': 'application/json;charset=utf-8',
            'X-CSRFToken': csrf_token,
        },
        "csrf_token": csrf_token,
        "session_length": settings.GEOREFERENCE_SESSION_LENGTH,
        "on_mobile": on_mobile(request)['on_mobile'],
        "user": user_info_from_request(request),
        "urls": internal_urls,
    }

def site_info(request):
    """ Return site name, build number, etc. """

    site = Site.objects.get_current()
    return {
        'SITE_NAME': site.name,
        'SITE_DOMAIN': site.domain,
        'BUILD_NUMBER': settings.BUILD_NUMBER,
    }
