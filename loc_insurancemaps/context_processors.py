from georeference.utils import analyze_url, full_reverse

from .models import Volume, get_volume

def loc_info(request):

    info = {
        "volume_ct": {
            "total": Volume.objects.all().count(),
            "started": Volume.objects.exclude(loaded_by=None).count(),
        }
    }

    resource_type, res_id = analyze_url(request)

    if res_id is not None:
        vol = get_volume(resource_type, res_id)
        info['volume_title'] = vol.__str__()
        info['volume_url'] = full_reverse('volume_summary', args=(vol.pk,))

    return info