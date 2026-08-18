from django.http import JsonResponse
from django.views import View

from ohmg.conf.http import JsonResponseNotFound
from ohmg.core.models import Map
from ohmg.core.utils import full_reverse

from .atlascope import generate_atlascope_footprints
from .iiif import IIIFResource


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
                    for i in [k for k in ls.get_layers()]
                ],
            }
        )


class AtlascopeDataView(View):
    def get(self, request, place, operation):
        data_name = request.GET.get("data-name")
        match operation:
            case "footprints":
                topo_json = generate_atlascope_footprints(place, override_data_name=data_name)
                return JsonResponse(topo_json)

            case "coverages":
                return JsonResponse(
                    [{"name": str(place), "center": place.get_center()}], safe=False
                )

            case _:
                return JsonResponseNotFound(
                    "invalid operation. must be 'footprints' or 'coverages'"
                )
