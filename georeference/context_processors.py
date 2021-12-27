from django.middleware import csrf

from .utils import analyze_url
from .proxy_models import get_georeferencing_summary

def georeference_info(request):

    resource_type, res_id = analyze_url(request)

    if None in [resource_type, res_id]:
        return {}

    info = get_georeferencing_summary(res_id)
    info['USER_AUTHENTICATED'] = request.user.is_authenticated
    info['CSRFTOKEN'] = csrf.get_token(request)

    return {
        'svelte_params': info,
    }
