from django.conf import settings
from georeference.utils import analyze_url, full_reverse
from georeference.models.resources import Document, Layer
from loc_insurancemaps.models import find_volume

def loc_info(request):

    info = {
        'volume_title': "",
        'volume_url': "",
        'newsletter_enabled': settings.ENABLE_NEWSLETTER,
    }
    vol = None

    resource_type, res_id = analyze_url(request)
    if res_id is not None:
        if resource_type == "document":
            try:
                item = Document.objects.get(pk=res_id)
            except:
                return info
        elif resource_type == "layer":
            res_id = res_id.replace("geonode:", "")
            try:
                item = Layer.objects.get(slug=res_id)
            except:
                return info
        vol = find_volume(item)
    if vol is not None:
        info['volume_title'] = vol.__str__()
        info['volume_url'] = full_reverse('volume_summary', args=(vol.pk,))

    return info
