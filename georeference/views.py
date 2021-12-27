import os
import json
import logging

from django.conf import settings
from django.shortcuts import render
from django.views import View
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from django.middleware import csrf
from django.contrib.gis.geos import Polygon

from georeference.tasks import (
    split_image_as_task,
    georeference_document_as_task,
)
from .models import (
    LayerMask,
    MaskSession,
    SplitSession,
    GeoreferenceSession,
)
from .proxy_models import (
    DocumentProxy,
    LayerProxy,
)
from .splitter import Splitter
from .georeferencer import Georeferencer


logger = logging.getLogger("geonode.georeference.views")

BadPostRequest = HttpResponseBadRequest("invalid post content")

class SummaryJSON(View):

    def get(self, request, docid):

        from .proxy_models import get_georeferencing_summary
        if docid:
            response = get_georeferencing_summary(docid)
            return JsonResponse(response)
        else:
            return JsonResponse({})

class SplitView(View):

    def get(self, request, docid):
        """
        Returns the splitting interface for this document.
        """

        doc_proxy = DocumentProxy(docid, raise_404_on_error=True)

        svelte_params = {
            "CSRFTOKEN": csrf.get_token(request),
            "DOCUMENT": doc_proxy.serialize(),
            "IMG_SIZE": doc_proxy.image_size,
            "INCOMING_CUTLINES": doc_proxy.cutlines,
            "USER_AUTHENTICATED": request.user.is_authenticated,
        }
        
        return render(
            request,
            "georeference/split.html",
            context={"svelte_params": svelte_params},
        )

    def post(self, request, docid):

        if not request.body:
            return BadPostRequest

        doc_proxy = DocumentProxy(docid, raise_404_on_error=True)

        body = json.loads(request.body)
        cutlines = body.get("lines", [])
        operation = body.get("operation", "preview")
        no_split = body.get("no_split")

        if operation == "preview":
            splitter = Splitter(image_file=doc_proxy.doc_file.path)
            segments = splitter.generate_divisions(cutlines)
            return JsonResponse({"success": True, "polygons": segments})

        elif operation == "submit":
            if no_split is True:
                segments = None
                cutlines = None
            else:
                splitter = Splitter(image_file=doc_proxy.doc_file.path)
                segments = splitter.generate_divisions(cutlines)

            session = SplitSession.objects.create(
                document=doc_proxy.resource,
                user=request.user,
                no_split_needed=no_split,
                segments_used=segments,
                cutlines_used=cutlines,
            )

            split_image_as_task.apply_async((session.pk, ), queue="update")

            return JsonResponse({"success":True})

        else:
            return BadPostRequest


class TrimView(View):

    def get(self, request, layeralternate):

        layer_proxy = LayerProxy(layeralternate, raise_404_on_error=True)

        gs = os.getenv("GEOSERVER_LOCATION", "http://localhost:8080/geoserver/")
        gs = gs.rstrip("/") + "/"
        geoserver_ows = f"{gs}ows/"

        svelte_params = {
            "LAYER": layer_proxy.serialize(),
            "CSRFTOKEN": csrf.get_token(request),
            "GEOSERVER_WMS": geoserver_ows,
            "MAPBOX_API_KEY": settings.MAPBOX_API_TOKEN,
            "INCOMING_MASK_COORDINATES": layer_proxy.mask_coords,
            "USER_AUTHENTICATED": request.user.is_authenticated,
        }

        return render(
            request,
            "georeference/trim.html",
            context={
                "svelte_params": svelte_params,
            }
        )

    def post(self, request, layeralternate):

        if not request.body:
            return BadPostRequest
            
        layer_proxy = LayerProxy(layeralternate, raise_404_on_error=True)

        body = json.loads(request.body)
        polygon_coords = body.get("mask_coords", [])
        operation = body.get("operation")

        if len(polygon_coords) >= 3:
            polygon = Polygon(polygon_coords)
        else:
            polygon = None

        if operation == "preview":

            if polygon is not None:
                preview_sld = LayerMask(
                    layer=layer_proxy.resource,
                    polygon=polygon,
                ).as_sld()
            else:
                preview_sld = None

            return JsonResponse({"success": True, "sld_content": preview_sld})

        elif operation == "submit":

            ts = MaskSession.objects.create(
                layer=layer_proxy.resource,
                user=request.user,
                polygon=polygon,
            )
            ts.run()
            return JsonResponse({"success": True})

        else:
            return BadPostRequest

class GeoreferenceView(View):

    def get(self, request, docid):
        """
        Returns the georeferencing interface for this document.
        """

        doc_proxy = DocumentProxy(docid, raise_404_on_error=True)

        username = request.user.username
        # this can go away once proper decorators are added that disallow
        # unauthenticated people from viewing the page
        if username == "":
            username = "<anonymous>"

        svelte_params = {
            "CSRFTOKEN": csrf.get_token(request),
            "DOCUMENT": doc_proxy.serialize(),
            "IMG_SIZE": doc_proxy.image_size,
            "INCOMING_GCPS": doc_proxy.gcps_geojson,
            "INCOMING_TRANSFORMATION": doc_proxy.transformation,
            "REGION_EXTENT": doc_proxy.get_best_region_extent(),
            "USERNAME": username,
            "MAPSERVER_ENDPOINT": settings.MAPSERVER_ENDPOINT,
            "MAPSERVER_LAYERNAME": doc_proxy.add_mapserver_layer(),
            "MAPBOX_API_KEY": settings.MAPBOX_API_TOKEN,
            "USER_AUTHENTICATED": request.user.is_authenticated,
        }

        return render(
            request,
            "georeference/georeference.html",
            context={
                'svelte_params': svelte_params,
            }
        )

    def post(self, request, docid):
        """
        Runs the georeferencing process for this document.
        """

        if not request.body:
            return BadPostRequest

        doc_proxy = DocumentProxy(docid, raise_404_on_error=True)

        body = json.loads(request.body)
        gcp_geojson = body.get("gcp_geojson", {})
        transformation = body.get("transformation", "poly1")
        operation = body.get("operation", "preview")

        response = {
            "status": "",
            "message": ""
        }

        # if preview mode, modify/create the vrt for this map.
        # the vrt layer should already served to the interface via mapserver,
        # and it will be automatically reloaded there.
        if operation == "preview":

            # prepare Georeferencer object
            g = Georeferencer(epsg_code=3857)
            g.load_gcps_from_geojson(gcp_geojson)
            g.set_transformation(transformation)
            try:
                out_path = g.georeference(
                    doc_proxy.doc_file.path,
                    out_format="VRT",
                )
                response["status"] = "success"
                response["message"] = "all good"
            except Exception as e:
                print("exception caught")
                print(e)
                response["status"] = "fail"
                response["message"] = str(e)
            return JsonResponse(response)

        elif operation == "submit":

            session = GeoreferenceSession.objects.create(
                document=doc_proxy.resource,
                user=request.user,
                gcps_used=gcp_geojson,
                transformation_used=transformation,
                crs_epsg_used=3857,
            )
            georeference_document_as_task.apply_async(
                (session.pk,),
                queue="update"
            )

            doc_proxy.remove_mapserver_layer()
            response["status"] = "success"
            response["message"] = "all good"
            return JsonResponse(response)

        elif operation == "cleanup":

            doc_proxy.remove_mapserver_layer()
            response["status"] = "success"
            response["message"] = "all good"
            return JsonResponse(response)

        else:
            return BadPostRequest

## DEPRECATED - IIIF is not currently implemented, retain for future reference.
def iiif2_endpoint(request, docid, iiif_object_requested):
    """ create a iiif v2 manifest, canvas, resource, or info.json object for a
    document image. info.json is not possible if an IIIF server is not enabled.
    """
    from django.template import loader
    from django.shortcuts import redirect
    from geonode.documents.models import Document
    from geonode.documents.views import _resolve_document
    from .utils import (
        document_as_iiif_resource,
        document_as_iiif_canvas,
        document_as_iiif_manifest,
    )

    IIIF_SERVER_ENABLED = getattr(settings, "IIIF_SERVER_ENABLED", False)

    document = _resolve_document(request, docid)
    if not isinstance(document, Document):
        return document

    if iiif_object_requested == "manifest":
        return JsonResponse(document_as_iiif_manifest(
            document,
            iiif_server=IIIF_SERVER_ENABLED,
        ))

    elif iiif_object_requested == "canvas":
        return JsonResponse(document_as_iiif_canvas(
            document,
            iiif_server=IIIF_SERVER_ENABLED,
        ))

    elif iiif_object_requested == "resource":
        return JsonResponse(document_as_iiif_resource(
            document,
            iiif_server=IIIF_SERVER_ENABLED,
        ))

    elif iiif_object_requested == "info":
        # if there is a iiif server set up, then this will redirect to that url
        # to supply the info.json generated there.
        if IIIF_SERVER_ENABLED is True:
            fname = os.path.basename(document.doc_file.name)
            info_url = f"{settings.IIIF_SERVER_LOCATION}/iiif/2/{fname}/info.json"
            return redirect(info_url)

        # if there is no iiif server, info.json is not supported.
        # see: https://github.com/IIIF/api/issues/1983
        else:
            return JsonResponse({
                "status": "not implemented",
                "message": "info.json is not available without a IIIF server."
            })

    else:
        return HttpResponse(
            loader.render_to_string(
                "404.html", context={
                }, request=request), status=404)
