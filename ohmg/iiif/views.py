from django.http import JsonResponse
from django.views import View

from ohmg.core.models import Map
from ohmg.core.utils import full_reverse
from .utils import IIIFResource


class IIIFSelectorView(View):
    def get(self, request, layerid):
        return JsonResponse(IIIFResource(layerid).get_selector())


class IIIFGCPView(View):
    def get(self, request, layerid):
        return JsonResponse(IIIFResource(layerid).get_gcps())


class IIIFResourceView(View):
    def get(self, request, layerid):
        trim = request.GET.get("trim", "false") == "true"
        extended = request.GET.get("extended", "false") == "true"
        resource = IIIFResource(layerid, trimmed=trim, extended=extended)
        return JsonResponse(resource.get_annotation())


class IIIFMosaicView(View):
    def get(self, request, mapid, layerset_category):
        ls = Map.objects.get(pk=mapid).get_layerset(layerset_category)
        trim = request.GET.get("trim", "false") == "true"
        extended = request.GET.get("extended", "false") == "true"
        return JsonResponse(
            {
                "id": full_reverse("iiif_canvas_view", args=(mapid, layerset_category)),
                "type": "AnnotationPage",
                "@context": [
                    "http://www.w3.org/ns/anno.jsonld",
                ],
                "label": f"Mosaic of {ls.category.display_name.lower()}, {ls.map}",
                "items": [
                    IIIFResource(i.pk, trimmed=trim, extended=extended).get_annotation()
                    for i in [k for k in ls.layer_set.all()]
                ],
            }
        )
