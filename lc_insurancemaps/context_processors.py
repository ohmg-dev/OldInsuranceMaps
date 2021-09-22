from django.conf import settings
from django.urls import reverse
from .utils.enumerations import STATE_CHOICES

def lc_svelte_params(request):
    """Global values to pass to templates"""

    lc_svelte = {
        "lc_svelte_params": {
            "STATE_CHOICES": STATE_CHOICES,
            "CITY_QUERY_URL": reverse('lc_api')
        }
    }
    return lc_svelte
