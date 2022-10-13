import os
import json
import logging

from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.views import View
from django.http import JsonResponse, HttpResponseBadRequest, Http404
from django.middleware import csrf
from django.contrib.gis.geos import Polygon

from geonode.layers.models import Layer as GNLayer

from georeference.tasks import (
    run_preparation_session,
    run_georeference_session,
)
from georeference.models.resources import (
    LayerMask,
    Document,
)
from georeference.models.sessions import (
    PrepSession,
    GeorefSession,
    TrimSession,
)
from georeference.proxy_models import (
    LayerProxy,
    get_info_panel_content,
    SessionLock,
)
from georeference.utils import MapServerManager
from georeference.georeferencer import Georeferencer
from georeference.splitter import Splitter

logger = logging.getLogger(__name__)

BadPostRequest = HttpResponseBadRequest("invalid post content")

class SummaryJSON(View):

    def get(self, request, resourceid):

        if resourceid:
            response = get_info_panel_content(resourceid)
            return JsonResponse(response)
        else:
            return JsonResponse({})

class SplitView(View):

    def get(self, request, docid):
        """
        Returns the splitting interface for this document.
        """

        # doc_proxy = DocumentProxy(docid, raise_404_on_error=True)
        # lock = doc_proxy.preparation_lock
        # sesh_id = None
        # if not lock.enabled:
        #     if request.user.is_authenticated:
        #         sesh = PrepSession.objects.create(
        #             document=doc_proxy.resource,
        #             user=request.user,
        #         )
        #         sesh.start()
        #         sesh_id = sesh.id
        #         lock.stage = "in-progress"
        #     else:
        #         lock.enabled = True
        #         lock.type = "unauthenticated"

        # override lock with new empty one - Oct 6th
        lock = SessionLock()
        sesh_id = 99999999

        document = get_object_or_404(Document, pk=docid)
        doc_data = document.serialize()

        split_params = {
            "LOCK": lock.as_dict,
            "SESSION_ID": sesh_id,
            "SESSION_LENGTH": settings.GEOREFERENCE_SESSION_LENGTH,
            "CSRFTOKEN": csrf.get_token(request),
            "DOCUMENT": doc_data,
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

        # doc_proxy = DocumentProxy(docid, raise_404_on_error=True)

        document = get_object_or_404(Document, pk=docid)

        body = json.loads(request.body)
        cutlines = body.get("lines")
        operation = body.get("operation")
        sesh_id = body.get("sesh_id", None)

        if operation == "preview":

            s = Splitter(image_file=document.file.path)
            # s = Splitter(image_file=doc_proxy.resource.doc_file.path)
            divisions = s.generate_divisions(cutlines)
            return JsonResponse({"success": True, "divisions": divisions})

        elif operation == "split":

            sesh, created = PrepSession.objects.get_or_create(doc=document)
            # sesh, created = PrepSession.objects.get_or_create(document=doc_proxy.resource)
            if sesh.user is None:
                sesh.user = request.user
            sesh.data['split_needed'] = True
            sesh.data['cutlines'] = cutlines
            sesh.save(update_fields=["data", "user"])
            logger.info(f"{sesh.__str__()} | begin run() as task")
            run_preparation_session.apply_async((sesh.pk, ), queue="update")
            return JsonResponse({"success":True})
        
        elif operation == "no_split":

            sesh, created = PrepSession.objects.get_or_create(doc=document)
            # sesh, created = PrepSession.objects.get_or_create(document=doc_proxy.resource)
            if sesh.user is None:
                sesh.user = request.user
            sesh.data['split_needed'] = False
            sesh.save(update_fields=["data", "user"])
            sesh.run()
            return JsonResponse({"success":True})

        elif operation == "cancel":

            try:
                sesh = PrepSession.objects.get(doc=document)
                # sesh = PrepSession.objects.get(document=doc_proxy.resource)
            except PrepSession.DoesNotExist:
                logger.warn("can't find PrepSession to delete.")
                return JsonResponse({"success":False, "message": "no session to cancel"})
            if sesh.stage != "input":
                msg = "can't cancel session that is past the input stage"
                logger.warn(f"{sesh.__str__()} | {msg}")
                return JsonResponse({"success":True, "message": msg})
            sesh.delete()
            return JsonResponse({"success":True})

        elif operation == "extend-session":

            try:
                sesh = PrepSession.objects.get(pk=sesh_id)
            except PrepSession.DoesNotExist:
                logger.warn("can't find PrepSession to delete.")
                return JsonResponse({"success":False, "message": "no session to cancel"})
            sesh.extend()
            return JsonResponse({"success":True})

        elif operation == "undo":

            try:
                sesh = PrepSession.objects.get(doc=document)
                # sesh = PrepSession.objects.get(document=doc_proxy.resource)
            except PrepSession.DoesNotExist:
                return JsonResponse({"success":False, "message": "no session to undo"})
            sesh.undo()
            return JsonResponse({"success":True})

        else:
            return BadPostRequest


class GeoreferenceView(View):

    def get(self, request, docid):
        """
        Returns the georeferencing interface for this document.
        """

        # doc_proxy = DocumentProxy(docid, raise_404_on_error=True)
        # if doc_proxy.resource.metadata_only is True:
        #     raise Http404
        # if doc_proxy.status in ["unprepared", "splitting"]:
        #     raise Http404
        # lock = doc_proxy.georeference_lock

        document = get_object_or_404(Document, pk=docid)
        if document.status in ["unprepared", "splitting", "split"]:
            raise Http404
        data = document.serialize(serialize_parent=False)

        # override lock with new empty one - Oct 6th
        lock = SessionLock()
        sesh_id = 99999999

        ## disable session creation for now - Oct 6th
        # sesh_id = None
        # if not lock.enabled:
        #     if request.user.is_authenticated:
        #         sesh = GeorefSession.objects.create(
        #             document=doc_proxy.resource,
        #             user=request.user,
        #         )
        #         sesh.start()
        #         sesh_id = sesh.pk
        #         lock.stage = "in-progress"
        #     else:
        #         lock.enabled = True
        #         lock.type = "unauthenticated"

        ms = MapServerManager()

        gs = os.getenv("GEOSERVER_LOCATION", "http://localhost:8080/geoserver/")
        gs = gs.rstrip("/") + "/"
        geoserver_ows = f"{gs}ows/"

        reference_layers_param = request.GET.get('reference', '')
        reference_layers = []
        for alt in reference_layers_param.split(","):
            if GNLayer.objects.filter(alternate=alt).exists():
                reference_layers.append(alt)

        extent_str = request.GET.get('extent', None)
        if extent_str is None:
            # hard-code Louisiana for now
            extent = (-94, 28, -88, 33)
        else:
            extent = tuple(extent_str.split(","))

        print(json.dumps(data, indent=1))

        georeference_params = {
            "LOCK": lock.as_dict,
            "SESSION_ID": sesh_id,
            "SESSION_LENGTH": settings.GEOREFERENCE_SESSION_LENGTH,
            "CSRFTOKEN": csrf.get_token(request),
            "DOCUMENT": data,
            "IMG_SIZE": data['image_size'],
            "INCOMING_GCPS": data['gcps_geojson'],
            "INCOMING_TRANSFORMATION": data['transformation'],
            "REGION_EXTENT": extent,
            "USERNAME": request.user.username,
            "MAPSERVER_ENDPOINT": ms.endpoint,
            "MAPSERVER_LAYERNAME": ms.add_layer(document.file.path),
            "MAPBOX_API_KEY": settings.MAPBOX_API_TOKEN,
            "GEOSERVER_WMS": geoserver_ows,
            "REFERENCE_LAYERS": reference_layers,
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

        document = get_object_or_404(Document, pk=docid)
        # doc_proxy = DocumentProxy(docid, raise_404_on_error=True)
        ms = MapServerManager()

        body = json.loads(request.body)
        gcp_geojson = body.get("gcp_geojson", {})
        transformation = body.get("transformation", "poly1")
        operation = body.get("operation", "preview")
        sesh_id = body.get("sesh_id", None)

        response = {
            "status": "",
            "message": ""
        }

        # if preview mode, modify/create the vrt for this map.
        # the vrt layer should already be served to the interface via mapserver,
        # and it will be automatically reloaded there.
        # allow this to happen without looking for or using a session
        if operation == "preview":

            # prepare Georeferencer object
            g = Georeferencer(epsg_code=3857)
            g.load_gcps_from_geojson(gcp_geojson)
            g.set_transformation(transformation)
            try:
                out_path = g.make_vrt(document.file.path)
                response["status"] = "success"
                response["message"] = "all good"
            except Exception as e:
                logger.error(e)
                response["status"] = "fail"
                response["message"] = str(e)
            return JsonResponse(response)

        if sesh_id is None:
            return JsonResponse({
                "success":False,
                "message": "no session id: view must be called on existing session"
            })

        try:
            sesh = GeorefSession.objects.get(pk=sesh_id)
        except GeorefSession.DoesNotExist:
            return JsonResponse({
                "success":False,
                "message": f"session {sesh_id} not found: view must be called existing on session"
            })

        if operation == "submit":

            sesh.data['epsg'] = 3857
            sesh.data['gcps'] = gcp_geojson
            sesh.data['transformation'] = transformation
            sesh.save(update_fields=["data"])
            logger.info(f"{sesh.__str__()} | begin run() as task")
            run_georeference_session.apply_async((sesh.pk, ), queue="update")

            ms.remove_layer(document.file.path)
            return JsonResponse({
                "success": True,
                "message": "all good",
            })

        elif operation == "extend-session":

            sesh.extend()
            return JsonResponse({"success":True})

        elif operation == "cancel":

            if sesh.stage != "input":
                msg = "can't cancel session that is past the input stage"
                logger.warn(f"{sesh.__str__()} | {msg}")
                return JsonResponse({"success":True, "message": msg})

            ms.remove_layer(document.file.path)
            sesh.delete()
            return JsonResponse({"success":True})

        else:
            return BadPostRequest


class TrimView(View):

    def get(self, request, layeralternate):

        layer_proxy = LayerProxy(layeralternate, raise_404_on_error=True)
        lock = layer_proxy.trim_lock

        sesh_id = None
        if not lock.enabled:
            if request.user.is_authenticated:
                sesh = TrimSession.objects.create(
                    layer=layer_proxy.resource,
                    user=request.user,
                )
                sesh.start()
                sesh_id = sesh.pk
                lock.stage = "in-progress"
            else:
                lock.enabled = True
                lock.type = "unauthenticated"

        gs = os.getenv("GEOSERVER_LOCATION", "http://localhost:8080/geoserver/")
        gs = gs.rstrip("/") + "/"
        geoserver_ows = f"{gs}ows/"

        trim_params = {
            "LOCK": lock.as_dict,
            "SESSION_ID": sesh_id,
            "SESSION_LENGTH": settings.GEOREFERENCE_SESSION_LENGTH,
            "LAYER": layer_proxy.serialize(),
            "CSRFTOKEN": csrf.get_token(request),
            "GEOSERVER_WMS": geoserver_ows,
            "MAPBOX_API_KEY": settings.MAPBOX_API_TOKEN,
            "INCOMING_MASK_COORDINATES": layer_proxy.mask_coords,
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
        sesh_id = body.get("sesh_id", None)

        if sesh_id is None:
            logger.warn(f"no session id in trim view post")
            return JsonResponse({
                "success":False,
                "message": "no session id: view must be called on existing session"
            })
        try:
            sesh = TrimSession.objects.get(pk=sesh_id)
        except TrimSession.DoesNotExist:
            logger.warn(f"invalid session id {sesh_id} in trim view post")
            return JsonResponse({
                "success":False,
                "message": f"session {sesh_id} not found: view must be called existing on session"
            })

        if operation in ["preview", "submit"]:
            if len(polygon_coords) < 3:
                return JsonResponse({"success": False, "message": "not enough coords"})
            try:
                mask = Polygon(polygon_coords)
            except ValueError as e:
                logger.warn(f"error in trim preview: {e}")
                return JsonResponse({"success": False, "message": str(e)})

        if operation == "preview":
            preview_sld = LayerMask(
                layer=layer_proxy.resource,
                polygon=mask,
            ).as_sld()
            return JsonResponse({"success": True, "sld_content": preview_sld})

        elif operation == "submit":

            sesh.data['mask_ewkt'] = mask.ewkt
            sesh.save()
            sesh.run()
            return JsonResponse({"success": True})

        elif operation == "cancel":

            if sesh.stage != "input":
                msg = "can't cancel session that is past the input stage"
                logger.warn(f"{sesh.__str__()} | {msg}")
                return JsonResponse({"success":True, "message": msg})

            sesh.delete()
            return JsonResponse({"success": True})

        elif operation == "extend-session":

            sesh.extend()
            return JsonResponse({"success":True})

        elif operation == "remove-mask":

            # first cancel the current session
            sesh.delete()
            # now remove the LayerMask.
            LayerMask.objects.filter(layer=layer_proxy.resource).delete()
            return JsonResponse({"success": True})

        else:
            return BadPostRequest
