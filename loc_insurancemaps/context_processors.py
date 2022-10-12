from georeference.utils import analyze_url, full_reverse

from .models import Volume, get_volume

def loc_info(request):

    resource_type, res_id = analyze_url(request)

    info = {}
    if res_id is not None:
        vol = get_volume(resource_type, res_id)
        if vol is not None:
            info['volume_title'] = vol.__str__()
            info['volume_url'] = full_reverse('volume_summary', args=(vol.pk,))
        else:
            info['volume_title'] = ""
            info['volume_url'] = ""

    return info
