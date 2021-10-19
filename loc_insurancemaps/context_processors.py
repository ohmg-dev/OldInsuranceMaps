from django.conf import settings
from django.urls import reverse
from .utils.enumerations import STATE_CHOICES

def lc_svelte_params(request):
    """Global values to pass to templates"""

    if request.user.is_superuser:
        user_type = "superuser"
    elif request.user.is_authenticated:
        user_type = "participant"
    else:
        user_type = "anonymous"

    lc_svelte = {
        "lc_svelte_params": {
            "STATE_CHOICES": STATE_CHOICES,
            "CITY_QUERY_URL": reverse('lc_api'),
            'USER_TYPE': user_type,
        }
    }
    return lc_svelte
