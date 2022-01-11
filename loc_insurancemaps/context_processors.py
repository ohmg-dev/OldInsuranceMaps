from georeference.utils import analyze_url, full_reverse

from .models import Volume, get_volume

def loc_info(request):

    info = {
        "volumes": {
            "total_ct": Volume.objects.all().count(),
            "started_ct": Volume.objects.exclude(loaded_by=None).count(),
            "id_list": list(Volume.objects.all().values_list("identifier", "city", "year", "volume_no")),
        }
    }

    resource_type, res_id = analyze_url(request)

    if res_id is not None:
        vol = get_volume(resource_type, res_id)
        info['volume_title'] = vol.__str__()
        info['volume_url'] = full_reverse('volume_summary', args=(vol.pk,))

    return info