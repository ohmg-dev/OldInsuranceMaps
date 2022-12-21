from django.conf import settings

from georeference.utils import full_reverse

def loc_info(request):

    if request.user.is_authenticated:
        user = {
            'is_authenticated': True,
            'name': request.user.username,
            'profile': full_reverse("profile_detail", args=(request.user.username, )),
        }
    else:
        user = {
            'is_authenticated': False
        }
    return {
        'newsletter_enabled': settings.ENABLE_NEWSLETTER,
        'navbar_params': {
            'USER': user
        }
    }
