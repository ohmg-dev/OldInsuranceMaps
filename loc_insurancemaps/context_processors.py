from georeference.utils import analyze_url, full_reverse

from .models import Volume, get_volume

def loc_info(request):

    volumes = Volume.objects.all()
    id_list = list(volumes.order_by("city", "year").values_list("identifier", "city", "year", "volume_no"))

    info = {
        "volumes": {
            "total_ct": volumes.count(),
            "started_ct": volumes.exclude(loaded_by=None).count(),
            "id_list": id_list,
        }
    }

    resource_type, res_id = analyze_url(request)

    if res_id is not None:
        vol = get_volume(resource_type, res_id)
        info['volume_title'] = vol.__str__()
        info['volume_url'] = full_reverse('volume_summary', args=(vol.pk,))

    return info