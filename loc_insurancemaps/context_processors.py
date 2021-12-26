from geonode.documents.models import Document
from georeference.proxy_models import DocumentProxy, LayerProxy
from georeference.utils import analyze_url, full_reverse
from .models import Volume, Sheet


def loc_info(request):

    info = {
        "volume_ct": Volume.objects.all().count(),
    }

    resource_type, res_id = analyze_url(request)

    if res_id is not None:
        if resource_type == "document":
            dp = DocumentProxy(res_id)
        elif resource_type == "layer":
            p = LayerProxy(res_id)
            dp = p.get_document_proxy()
        if dp.parent_doc is not None:
            doc = dp.parent_doc.get_document()
        else:
            doc = dp.get_document()
        volume = Sheet.objects.get(document=doc).volume
        info['volume_title'] = volume.__str__()
        info['volume_url'] = full_reverse('volume_summary', args=(volume.pk,))

    return info