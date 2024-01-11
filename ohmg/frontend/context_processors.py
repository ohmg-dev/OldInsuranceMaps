from django.conf import settings
from django.contrib.sites.models import Site
from ohmg.utils import full_reverse

from ohmg.accounts.schemas import UserSchema

def loc_info(request):

    try:
        user = request.user
    except AttributeError:
        user = None
    if user and user.is_authenticated:
        user_info = UserSchema.from_orm(user).dict()
        user_info['is_authenticated'] = True
    else:
        user_info = {
            'is_authenticated': False
        }
    return {
        'navbar_params': {
            'USER': user_info
        },
        'footer_params': {},
    }

def general(request):
    """ neifnef """
    site = Site.objects.get_current()
    return {
        'SITE_NAME': site.name,
        'SITE_DOMAIN': site.domain,
        'BUILD_NUMBER': settings.BUILD_NUMBER,
    }
