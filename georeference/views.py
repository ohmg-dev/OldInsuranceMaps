import json
import logging

from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.views import View
from django.http import JsonResponse, HttpResponseBadRequest
from django.middleware import csrf

from georeference.tasks import (
    run_preparation_session,
    run_georeference_session,
)
from georeference.models.resources import (
    Layer,
    Document,
    ItemBase,
)
from georeference.models.sessions import (
    PrepSession,
    GeorefSession,
)
from georeference.utils import MapServerManager
from georeference.georeferencer import Georeferencer
from georeference.splitter import Splitter

from loc_insurancemaps.models import find_volume

logger = logging.getLogger(__name__)

BadPostRequest = HttpResponseBadRequest("invalid post content")

class SplitView(View):

    def get(self, request, docid):
        """
        Returns the splitting interface for this document.
        """

        document = get_object_or_404(Document, pk=docid)
        # if the document is not currently locked and there is a logged in user,
        # create a new session
        if not document.lock_enabled and request.user.is_authenticated and document.status == "unprepared":
            session = PrepSession.objects.create(
                doc=document,
                user=request.user
            )
            session.start()
        doc_data = document.serialize()

        volume = find_volume(document)
        volume_json = volume.serialize()

        split_params = {
            "USER": "" if not request.user.is_authenticated else request.user.username,
            "SESSION_LENGTH": settings.GEOREFERENCE_SESSION_LENGTH,
            "CSRFTOKEN": csrf.get_token(request),
            "DOCUMENT": doc_data,
            "VOLUME": volume_json,
        }
        
        return render(
            request,
            "georeference/split.html",
            context={
                "split_params": split_params
            },
        )

    def post(self, request, docid):

        if not request.body:
            return BadPostRequest

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

            try:
                sesh = PrepSession.objects.get(pk=sesh_id)
            except PrepSession.DoesNotExist:
                logger.warn("can't find PrepSession to delete.")
                return JsonResponse({"success":False, "message": "no session found"})
            sesh.data['split_needed'] = True
            sesh.data['cutlines'] = cutlines
            sesh.save(update_fields=["data"])
            logger.info(f"{sesh.__str__()} | begin run() as task")
            run_preparation_session.apply_async((sesh.pk, ), queue="update")
            return JsonResponse({"success":True})

        elif operation == "no_split":

            # if the request is made from the Split interface, then a sesh_ic
            # should have been passed along (use it to find the sesh)
            if sesh_id is not None:
                try:
                    sesh = PrepSession.objects.get(pk=sesh_id)
                    # sesh = PrepSession.objects.get(document=doc_proxy.resource)
                except PrepSession.DoesNotExist:
                    logger.warn("can't find PrepSession to delete.")
                    return JsonResponse({"success":False, "message": "no session to cancel"})
            # otherwise this request was made straight from the volume summary or
            # doc detail, so a new session must be created now
            # AS YET NOT FULLY TESTED
            else:
                sesh = PrepSession.objects.create(
                    doc=document,
                    user=request.user,
                    user_input_duration=0,
                )
                sesh.start()

            sesh.data['split_needed'] = False
            sesh.save(update_fields=["data"])
            sesh.run()
            return JsonResponse({"success":True})

        elif operation == "cancel":

            try:
                sesh = PrepSession.objects.get(pk=sesh_id)
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

            document.extend_lock()
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

        doc = get_object_or_404(Document, pk=docid)
        # if the document is not currently locked and there is a logged in user,
        # create a new session
        if not doc.lock_enabled and request.user.is_authenticated and \
            doc.status in ["prepared", "georeferenced"]:
            session = GeorefSession.objects.create(
                doc=doc,
                user=request.user
            )
            session.start()
        doc_data = doc.serialize()

        volume = find_volume(doc)
        volume_json = volume.serialize()

        ms = MapServerManager()

        # reference_layers_param = request.GET.get('reference', '')
        # reference_layers = []
        # for alt in reference_layers_param.split(","):
        #     if GNLayer.objects.filter(alternate=alt).exists():
        #         reference_layers.append(alt)

        georeference_params = {
            "USER": "" if not request.user.is_authenticated else request.user.username,
            "SESSION_LENGTH": settings.GEOREFERENCE_SESSION_LENGTH,
            "CSRFTOKEN": csrf.get_token(request),
            "DOCUMENT": doc_data,
            "VOLUME": volume_json,
            # "REGION_EXTENT": extent,
            "MAPSERVER_ENDPOINT": ms.endpoint,
            "MAPSERVER_LAYERNAME": ms.add_layer(doc.file.path),
            "MAPBOX_API_KEY": settings.MAPBOX_API_TOKEN,
            ## these variables will be reevaluated when reference layers re-implemented
            # "GEOSERVER_WMS": geoserver_ows,
            # "REFERENCE_LAYERS": reference_layers,
            # "TITILER_HOST": settings.TITILER_HOST,
        }

        return render(
            request,
            "georeference/georeference.html",
            context={
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

class ResourceView(View):

    def get(self, request, pk):

        resource = get_object_or_404(ItemBase, pk=pk)
        if resource.type == 'document':
            resource = Document.objects.get(pk=pk)
        elif resource.type == 'layer':
            resource = Layer.objects.get(pk=pk)

        split_summary = resource.get_split_summary()
        georeference_summary = resource.get_georeference_summary()
        sessions_json = resource.get_sessions(serialize=True)
        resource_json = resource.serialize()

        volume = find_volume(resource)
        volume_json = None
        if volume is not None:
            volume_json = volume.serialize()

        return render(
            request,
            "georeference/resource.html",
            context={
                'resource_params': {
                    'REFRESH_URL': None,
                    'RESOURCE': resource_json,
                    'VOLUME': volume_json,
                    'CSRFTOKEN': csrf.get_token(request),
                    'USER_AUTHENTICATED': request.user.is_authenticated,
                    "SPLIT_SUMMARY": split_summary,
                    "GEOREFERENCE_SUMMARY": georeference_summary,
                    "SESSION_HISTORY": sessions_json,
                    "MAPBOX_API_KEY": settings.MAPBOX_API_TOKEN,
                    "TITILER_HOST": settings.TITILER_HOST,
                }
            }
        )
