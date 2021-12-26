from .utils import analyze_url
from .proxy_models import get_georeferencing_summary

def georeference_info(request):

    resource_type, res_id = analyze_url(request)

    if None in [resource_type, res_id]:
        return {}

    return {
        'svelte_params': get_georeferencing_summary(res_id),
    }
