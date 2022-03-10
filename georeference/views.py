import os
import json
import logging

from django.conf import settings
from django.shortcuts import render
from django.views import View
from django.http import JsonResponse, HttpResponseBadRequest
from django.middleware import csrf
from django.contrib.gis.geos import Polygon

from georeference.tasks import (
    split_image_as_task,
    georeference_document_as_task,
    run_preparation_session,
    run_georeference_session,
)
from .models import (
    LayerMask,
    MaskSession,
    SplitEvaluation,
    GeoreferenceSession,
    PrepSession,
    GeorefSession,
    TrimSession,
)
from .proxy_models import (
    DocumentProxy,
    LayerProxy,
    get_georeferencing_summary,
)
from .utils import MapServerManager
from .georeferencer import Georeferencer
from .splitter import Splitter


logger = logging.getLogger("geonode.georeference.views")

BadPostRequest = HttpResponseBadRequest("invalid post content")

class SummaryJSON(View):

    def get(self, request, docid):

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
        lock = doc_proxy.preparation_lock

        if not lock.enabled:
            if request.user.is_authenticated:
                sesh = PrepSession.objects.create(
                    document=doc_proxy.resource,
                    user=request.user,
                )
                sesh.start()
                lock.stage = "in-progress"
            else:
                lock.enabled = True
                lock.type = "unauthenticated"

        split_params = {
            "LOCK": lock.as_dict,
            "CSRFTOKEN": csrf.get_token(request),
            "DOCUMENT": doc_proxy.serialize(),
            "IMG_SIZE": doc_proxy.image_size,
            "INCOMING_CUTLINES": doc_proxy.cutlines,
        }
        
        return render(
            request,
            "georeference/split.html",
            context={
                "preamble_params": {}, # overwrite the default with empty
                "split_params": split_params
            },
        )

    def post(self, request, docid):

        if not request.body:
            return BadPostRequest

        doc_proxy = DocumentProxy(docid, raise_404_on_error=True)

        body = json.loads(request.body)
        cutlines = body.get("lines")
        operation = body.get("operation")

        if operation == "preview":

            s = Splitter(image_file=doc_proxy.resource.doc_file.path)
            divisions = s.generate_divisions(cutlines)
            return JsonResponse({"success": True, "divisions": divisions})

        elif operation == "split":

            sesh, created = PrepSession.objects.get_or_create(document=doc_proxy.resource)
            if sesh.user is None:
                sesh.user = request.user
            sesh.data['split_needed'] = True
            sesh.data['cutlines'] = cutlines
            sesh.save(update_fields=["data", "user"])
            run_preparation_session.apply_async((sesh.pk, ), queue="update")
            return JsonResponse({"success":True})
        
        elif operation == "no_split":

            sesh, created = PrepSession.objects.get_or_create(document=doc_proxy.resource)
            if sesh.user is None:
                sesh.user = request.user
            sesh.data['split_needed'] = False
            sesh.save(update_fields=["data", "user"])
            sesh.run()
            return JsonResponse({"success":True})

        elif operation == "cancel":

            try:
                sesh = PrepSession.objects.get(document=doc_proxy.resource)
            except PrepSession.DoesNotExist:
                return JsonResponse({"success":False, "msg": "no session to cancel"})
            sesh.cancel()
            return JsonResponse({"success":True})

        else:
            return BadPostRequest


class TrimView(View):

    def get(self, request, layeralternate):

        layer_proxy = LayerProxy(layeralternate, raise_404_on_error=True)

        gs = os.getenv("GEOSERVER_LOCATION", "http://localhost:8080/geoserver/")
        gs = gs.rstrip("/") + "/"
        geoserver_ows = f"{gs}ows/"

        trim_params = {
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
                "preamble_params": {}, # overwrite the default with empty
                "trim_params": trim_params,
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
        ms = MapServerManager()

        georeference_params = {
            "CSRFTOKEN": csrf.get_token(request),
            "DOCUMENT": doc_proxy.serialize(),
            "IMG_SIZE": doc_proxy.image_size,
            "INCOMING_GCPS": doc_proxy.gcps_geojson,
            "INCOMING_TRANSFORMATION": doc_proxy.transformation,
            "REGION_EXTENT": doc_proxy.get_best_region_extent(),
            "USERNAME": request.user.username,
            "MAPSERVER_ENDPOINT": ms.endpoint,
            "MAPSERVER_LAYERNAME": ms.add_layer(doc_proxy.doc_file.path),
            "MAPBOX_API_KEY": settings.MAPBOX_API_TOKEN,
            "USER_AUTHENTICATED": request.user.is_authenticated,
        }

        return render(
            request,
            "georeference/georeference.html",
            context={
                'preamble_params': {}, # overwrite the default with empty
                'georeference_params': georeference_params,
            }
        )

    def post(self, request, docid):
        """
        Runs the georeferencing process for this document.
        """

        if not request.body:
            return BadPostRequest

        doc_proxy = DocumentProxy(docid, raise_404_on_error=True)
        ms = MapServerManager()

        body = json.loads(request.body)
        gcp_geojson = body.get("gcp_geojson", {})
        transformation = body.get("transformation", "poly1")
        operation = body.get("operation", "preview")

        response = {
            "status": "",
            "message": ""
        }

        # if preview mode, modify/create the vrt for this map.
        # the vrt layer should already be served to the interface via mapserver,
        # and it will be automatically reloaded there.
        if operation == "preview":

            # prepare Georeferencer object
            g = Georeferencer(epsg_code=3857)
            g.load_gcps_from_geojson(gcp_geojson)
            g.set_transformation(transformation)
            try:
                out_path = g.make_vrt(doc_proxy.doc_file.path)
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

            ms.remove_layer(doc_proxy.doc_file.path)
            response["status"] = "success"
            response["message"] = "all good"
            return JsonResponse(response)

        elif operation == "cleanup":

            ms.remove_layer(doc_proxy.doc_file.path)
            response["status"] = "success"
            response["message"] = "all good"
            return JsonResponse(response)

        else:
            return BadPostRequest
