import os
import json
from datetime import datetime
import logging

from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry
from django.shortcuts import render, get_object_or_404
from django.views import View
from django.http import JsonResponse, HttpResponseBadRequest
from django.middleware import csrf

from ohmg.georeference.tasks import (
    run_preparation_session,
    run_georeference_session,
)
from ohmg.georeference.models import (
    Document,
    GCPGroup,
    PrepSession,
    GeorefSession,
    ItemBase,
)
from ohmg.georeference.georeferencer import Georeferencer
from ohmg.georeference.splitter import Splitter
from ohmg.georeference.tasks import delete_preview_vrt

from ohmg.loc_insurancemaps.models import find_volume, Volume

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
            run_preparation_session.delay(sesh.pk)
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
            except Exception as e:
                return JsonResponse({"success":False, "message": str(e)})
            try:
                sesh.undo()
                vol = find_volume(document)
                vol.refresh_lookups()
            except Exception as e:
                return JsonResponse({"success":False, "message": str(e)})
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
            "MAPBOX_API_KEY": settings.MAPBOX_API_TOKEN,
            ## these variables will be reevaluated when reference layers re-implemented
            # "REFERENCE_LAYERS": reference_layers,
            "TITILER_HOST": settings.TITILER_HOST,
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

        body = json.loads(request.body)
        gcp_geojson = body.get("gcp_geojson", {})
        transformation = body.get("transformation", "poly1")
        projection = body.get("projection", "EPSG:3857")
        operation = body.get("operation", "preview")
        sesh_id = body.get("sesh_id", None)
        cleanup_preview = body.get("cleanup_preview", None)

        response = {
            "status": "",
            "message": ""
        }

        def _generate_preview_id(request, sesh_id):

            try:
                ip_val = request.META.get('REMOTE_ADDR', '0.0.0.0.').replace(".", "-")
            except Exception as e:
                logger.warn(e)
                ip_val = "000000000"

            sesh_val = 0
            if sesh_id:
                sesh_val = sesh_id

            return f"{ip_val}-{sesh_val}-{int(datetime.now().timestamp())}"

        def _cleanup_preview(document, previous_url):
            """ Run this deletion through celery, so that it doesn't delay
            the return of whatever function called it. """
            if previous_url:
                delete_preview_vrt.delay(document.file.path, previous_url)

        def _get_georef_session(sesh_id):

            try:
                sesh = GeorefSession.objects.get(pk=sesh_id)
            except GeorefSession.DoesNotExist:
                sesh = None
            return sesh

        SESSION_NOT_FOUND_RESPONSE = JsonResponse({
            "success":False,
            "message": f"session {sesh_id} not found: {operation} must be called with existing session"
        })

        # if preview mode, modify/create the vrt for this map.
        # allow this to happen without looking for or using a session
        if operation == "preview":

            # prepare Georeferencer object
            g = Georeferencer(
                crs=projection,
                gcps_geojson=gcp_geojson,
                transformation=transformation,
            )
            preview_id = _generate_preview_id(request, sesh_id)
            try:
                out_path = g.warp(document.file.path, return_vrt=True, preview_id=preview_id)
                out_path_relative = os.path.join(os.path.dirname(document.file.url), os.path.basename(out_path))
                preview_url = settings.MEDIA_HOST.rstrip("/") + out_path_relative
                response["status"] = "success"
                response["message"] = "all good"
                response["preview_url"] = preview_url
                # queue clean up of the last preview
                _cleanup_preview(document, cleanup_preview)
            except Exception as e:
                logger.error(e)
                response["status"] = "fail"
                response["message"] = str(e)
            return JsonResponse(response)

        elif operation == "ungeoreference":

            if not request.user.is_staff:
                return JsonResponse({
                    "success":False,
                    "message": "user not authorized for this operation"
                })
            
            sessions = GeorefSession.objects.filter(doc=document)
            for s in sessions:
                s.delete()
            layer = document.get_layer()
            if layer:
                layer.delete()
            try:
                gcp_group = GCPGroup.objects.get(doc=document)
                gcp_group.delete()
            except GCPGroup.DoesNotExist:
                pass
            document.set_status("prepared")
            vol = find_volume(document)
            vol.refresh_lookups()
            return JsonResponse({"success":True})

        elif operation == "submit":

            sesh = _get_georef_session(sesh_id)
            if sesh:
                # ultimately, should be putting the whole "EPSG:3857"
                # in the session data, but for now stick with just the number
                # see models.sessions.py line 510
                epsg_code = int(projection.split(":")[1])
                sesh.data['epsg'] = epsg_code
                sesh.data['gcps'] = gcp_geojson
                sesh.data['transformation'] = transformation
                sesh.save(update_fields=["data"])
                logger.info(f"{sesh.__str__()} | begin run() as task")
                run_georeference_session.apply_async((sesh.pk,))
                print('task should be running')
                _cleanup_preview(document, cleanup_preview)
                return JsonResponse({
                    "success": True,
                    "message": "all good",
                })

            else:
                return SESSION_NOT_FOUND_RESPONSE

        elif operation == "set-status":

            if request.user.is_authenticated:
                new_status = body.get("status", None)
                if new_status:
                    document.set_status(new_status)
                return JsonResponse({
                    "success": True,
                    "message": "all good",
                })

            else:
                return JsonResponse({
                    "success": False,
                    "message": "must be authenticated to perform this operation",
                })

        elif operation == "extend-session":

            sesh = _get_georef_session(sesh_id)
            if sesh:
                ## extend the lock expiration time on doc and lyr instance 
                ## attached to this session
                sesh.extend_locks()
                return JsonResponse({"success":True})
            else:
                return SESSION_NOT_FOUND_RESPONSE

        elif operation == "cancel":

            sesh = _get_georef_session(sesh_id)
            if sesh:
                if sesh.stage != "input":
                    msg = "can't cancel session that is past the input stage"
                    logger.warn(f"{sesh.__str__()} | {msg}")
                    return JsonResponse({"success":True, "message": msg})

                sesh.delete()

            _cleanup_preview(document, cleanup_preview)
            return JsonResponse({"success":True})

        else:
            return BadPostRequest


class MultiMaskView(View):

    def post(self, request, volumeid):

        volume = get_object_or_404(Volume, pk=volumeid)

        body = json.loads(request.body)
        multimask = body.get('multiMask')

        # data validation
        errors = []
        if multimask is not None and isinstance(multimask, dict):
            for k, v in multimask.items():
                try:
                    geom_str = json.dumps(v['geometry'])
                    g = GEOSGeometry(geom_str)
                    if not g.valid:
                        logger.error(f"{volumeid} | invalid mask: {k} - {g.valid_reason}")
                        errors.append((k, g.valid_reason))
                except Exception as e:
                    logger.error(f"{volumeid} | improper GeoJSON in multimask: {k}")
                    errors.append((k, e))
        if errors:
            response = {
                "status": "error",
                "errors": errors,
            }
        else:
            volume.multimask = multimask
            volume.save()
            response = {
                "status": "ok",
                "volume_json": volume.serialize()
            }

        return JsonResponse(response)


class AnnotationSetView(View):

    def post(self, request):

        if not request.body:
            return BadPostRequest

        body = json.loads(request.body)
        operation = body.get("operation")
        resource_id = body.get("resourceId")
        volume_id = body.get("volumeId")
        category = body.get("categorySlug")
        multimask_geojson = body.get('multimaskGeoJSON')

        response = {
            "status": "",
            "message": ""
        }

        if operation == "update":
            v = get_object_or_404(Volume, pk=volume_id)
            r = get_object_or_404(ItemBase, pk=resource_id)

            try:
                annoset = v.get_annotation_set(category, create=True)
                r.update_vrs(annoset)
                response['status'] = "success"
                response['message'] = f"{resource_id} added to {category} annotation set"

            except Exception as e:
                logger.error(e)
                response['status'] = "fail"
                response['message'] = str(e)

        if operation == "set-mask":

            v = get_object_or_404(Volume, pk=volume_id)
            annoset = v.get_annotation_set(category)

            errors = annoset.update_multimask_from_geojson(multimask_geojson)

            if errors:
                response["status"] = "fail"
                response["message"] = errors
            else:
                response["status"] = "success"

        return JsonResponse(response)
