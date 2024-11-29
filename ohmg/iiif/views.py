from django.conf import settings
from django.http import JsonResponse
from django.views import View

from ohmg.core.models import Map, Region
from ohmg.core.utils import full_reverse
from .utils import (
    region_as_iiif_resource,
    document_as_iiif_canvas,
    document_as_iiif_manifest,
)

# Create your views here.
## DEPRECATED - IIIF is not currently implemented, retain for future reference.
# def iiif2_endpoint(request, docid, iiif_object_requested):
#     """ create a iiif v2 manifest, canvas, resource, or info.json object for a
#     document image. info.json is not possible if an IIIF server is not enabled.
#     """
    

#     IIIF_SERVER_ENABLED = getattr(settings, "IIIF_SERVER_ENABLED", False)

#     document = _resolve_document(request, docid)
#     if not isinstance(document, Document):
#         return document

#     if iiif_object_requested == "manifest":
#         return JsonResponse(document_as_iiif_manifest(
#             document,
#             iiif_server=IIIF_SERVER_ENABLED,
#         ))

#     elif iiif_object_requested == "canvas":
#         return JsonResponse(document_as_iiif_canvas(
#             document,
#             iiif_server=IIIF_SERVER_ENABLED,
#         ))

#     elif iiif_object_requested == "resource":
#         return JsonResponse(document_as_iiif_resource(
#             document,
#             iiif_server=IIIF_SERVER_ENABLED,
#         ))

#     elif iiif_object_requested == "info":
#         # if there is a iiif server set up, then this will redirect to that url
#         # to supply the info.json generated there.
#         if IIIF_SERVER_ENABLED is True:
#             fname = os.path.basename(document.doc_file.name)
#             info_url = f"{settings.IIIF_SERVER_LOCATION}/iiif/2/{fname}/info.json"
#             return redirect(info_url)

#         # if there is no iiif server, info.json is not supported.
#         # see: https://github.com/IIIF/api/issues/1983
#         else:
#             return JsonResponse({
#                 "status": "not implemented",
#                 "message": "info.json is not available without a IIIF server."
#             })

#     else:
#         return HttpResponse(
#             loader.render_to_string(
#                 "404.html", context={
#                 }, request=request), status=404)

class IIIFResourceView(View):

    def get(self, request, regionid):
        region = Region.objects.get(pk=regionid)
        return JsonResponse(region_as_iiif_resource(region))

class IIIFCanvasView(View):

    def get(self, request, mapid, layerset_category):
        ls = Map.objects.get(pk=mapid).get_layerset(layerset_category)
        print(ls)
        print(ls.layers.all())
        return JsonResponse({
            "id": full_reverse("iiif_canvas_view", args=(mapid, layerset_category)),
            "type": "AnnotationPage",
            "@context": "http://www.w3.org/ns/anno.jsonld",
            "items": [region_as_iiif_resource(i) for i in [k.region for k in ls.layers.all()]],
        })