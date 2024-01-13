from django.conf import settings
from django.contrib.sites.models import Site

from ohmg.accounts.schemas import UserSchema

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

def navbar_footer_params(request):
    """ Build the params passed to the Navbar and Footer Svelte components."""

    return {
        'navbar_params': {
            'USER': user_info_from_request(request)
        },
        'footer_params': {},
    }

def site_info(request):
    """ Return site name, build number, etc. """

    site = Site.objects.get_current()
    return {
        'SITE_NAME': site.name,
        'SITE_DOMAIN': site.domain,
        'BUILD_NUMBER': settings.BUILD_NUMBER,
    }
