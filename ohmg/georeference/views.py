import os
import json
from datetime import datetime
import logging

from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.views import View
from django.http import JsonResponse, HttpResponseBadRequest

from ohmg.core.context_processors import generate_ohmg_context
from ohmg.core.utils import time_this
from ohmg.georeference.tasks import (
    # these are the old commands, retain for now
    run_georeference_session,
    run_preparation_session,
    # these are the new commands, use from now on
    run_georeferencing_as_task,
    run_preparation_as_task,
    # this is a temporary task used to create and link a new layer
    # to a new georef session
    patch_new_layer_to_session,
)
from ohmg.georeference.models import (
    Document as DocumentOld,
    GCPGroup,
    PrepSession,
    GeorefSession,
    LayerSet,
)
from ohmg.core.api.schemas import (
    DocumentFullSchema,
    LayerSetSchema,
    MapFullSchema,
    MapListSchema,
    RegionFullSchema,
)
from ohmg.core.models import (
    Region,
    Document,
    Layer,
    Map,
)
from ohmg.georeference.operations.sessions import run_preparation
from ohmg.georeference.georeferencer import Georeferencer
from ohmg.georeference.splitter import Splitter
from ohmg.georeference.tasks import delete_preview_vrt

from ohmg.loc_insurancemaps.models import find_volume

logger = logging.getLogger(__name__)

BadPostRequest = HttpResponseBadRequest("invalid post content")

class SplitView(View):

    @time_this
    def get(self, request, docid):
        """
        Returns the splitting interface for this document.
        """

        document = get_object_or_404(Document, pk=docid)
        
        # if the document is not currently locked and there is a logged in user,
        # create a new session
        if not document.lock and request.user.is_authenticated:
            session = PrepSession.objects.create(
                user=request.user,
                doc2=document
            )
            session.start()

        # serialize the document after the session has been created, this will get the new lock.
        document_json = DocumentFullSchema.from_orm(document).dict()

        split_params = {
            "CONTEXT": generate_ohmg_context(request),
            "DOCUMENT": document_json,
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

        sesh = None
        if sesh_id is not None:
            try:
                sesh = PrepSession.objects.get(pk=sesh_id)
            except PrepSession.DoesNotExist:
                logger.warn(f"can't find PrepSession ({sesh_id}), expected for Document {document.pk}")
                return JsonResponse({"success":False, "message": "no session found"})

        if operation == "preview":

            s = Splitter(image_file=document.file.path)
            divisions = s.generate_divisions(cutlines)
            return JsonResponse({"success": True, "divisions": divisions})

        elif operation == "split":

            sesh.data['split_needed'] = True
            sesh.data['cutlines'] = cutlines
            sesh.save(update_fields=["data"])
            logger.info(f"{sesh.__str__()} | begin run() as task")
            run_preparation_as_task.apply_async((sesh.pk,))
            # run_preparation_session.apply_async((sesh.pk,),
            #     link=run_preparation_as_task.s()
            # )
            return JsonResponse({"success":True})

        elif operation == "no_split":

            # sesh could be None if this post has been made directly from an overview page,
            # not from the split interface where a session will have already been made.
            if sesh is None:
                sesh = PrepSession.objects.create(
                    doc2=document,
                    user=request.user,
                    user_input_duration=0,
                )
                sesh.start()

            sesh.data['split_needed'] = False
            sesh.save(update_fields=["data"])
            # sesh.run()
            new_region = run_preparation(sesh)[0]

            return JsonResponse({
                "success":True,
                "region_id": new_region.pk,
            })

        elif operation == "cancel":

            if sesh.stage != "input":
                msg = "can't cancel session that is past the input stage"
                logger.warn(f"{sesh.__str__()} | {msg}")
                return JsonResponse({"success":True, "message": msg})
            sesh.delete()
            return JsonResponse({"success":True})

        elif operation == "extend-session":

            sesh.extend_locks2()
            return JsonResponse({"success":True})

        elif operation == "undo":
            try:
                sesh = PrepSession.objects.get(doc=document)
            except Exception as e:
                return JsonResponse({"success":False, "message": str(e)})
            try:
                sesh.undo()
                sesh.doc2.map.update_item_lookup()
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

        region = get_object_or_404(Region,  pk=docid)

        # if the region is not currently locked and there is a logged in user,
        # create a new session
        if not region.lock and request.user.is_authenticated:
            session = GeorefSession.objects.create(
                reg2=region,
                user=request.user,
            )
            if hasattr(region, 'layer'):
                session.lyr2 = region.layer
            session.start()

        region_json = RegionFullSchema.from_orm(region).dict()

        # volume = find_volume(doc)
        # volume_json = volume.serialize()

        map_json = MapFullSchema.from_orm(region.map).dict()

        annoset_main = LayerSetSchema.from_orm(region.document.map.get_layerset('main-content')).dict()
        annoset_keymap = None
        akm = region.document.map.get_layerset('key-map')
        if akm:
            annoset_keymap = LayerSetSchema.from_orm(akm).dict()

        georeference_params = {
            "CONTEXT": generate_ohmg_context(request),
            "REGION": region_json,
            "VOLUME": map_json,
            "ANNOSET_MAIN": annoset_main,
            "ANNOSET_KEYMAP": annoset_keymap,
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

        region = get_object_or_404(Region, pk=docid)

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

        def _cleanup_preview(region, previous_url):
            """ Run this deletion through celery, so that it doesn't delay
            the return of whatever function called it. """
            if previous_url:
                delete_preview_vrt.delay(region.file.path, previous_url)

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
                out_path = g.warp(region.file.path, return_vrt=True, preview_id=preview_id)
                out_path_relative = os.path.join(os.path.dirname(region.file.url), os.path.basename(out_path))
                preview_url = settings.MEDIA_HOST.rstrip("/") + out_path_relative
                response["status"] = "success"
                response["message"] = "all good"
                response["preview_url"] = preview_url
                # queue clean up of the last preview
                _cleanup_preview(region, cleanup_preview)
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
            
            sessions = GeorefSession.objects.filter(reg2=region)
            for s in sessions:
                s.delete()
            if hasattr(region, 'layer'):
                region.layer.delete()
            try:
                gcp_group = GCPGroup.objects.get(region=region)
                gcp_group.delete()
            except GCPGroup.DoesNotExist:
                pass
            region.georeferenced = False
            region.save()
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
                run_georeferencing_as_task.apply_async((sesh.pk,))
                # run_georeference_session.apply_async((sesh.pk,),
                #     link=patch_new_layer_to_session.s()
                # )

                _cleanup_preview(region, cleanup_preview)
                return JsonResponse({
                    "success": True,
                    "message": "all good",
                })

            else:
                return SESSION_NOT_FOUND_RESPONSE

        elif operation == "set-status":
            # TODO: this functionality should be moved somewhere else.
            if request.user.is_authenticated:
                change_to = body.get("status", None)
                if change_to == "nonmap":
                    region.is_map = False
                    region.save()
                if change_to == "prepared":
                    region.is_map = True
                    region.save()
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
                sesh.extend_locks2()
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

            _cleanup_preview(region, cleanup_preview)
            return JsonResponse({"success":True})

        else:
            return BadPostRequest


class LayerSetView(View):

    def post(self, request):

        if not request.body:
            return BadPostRequest

        body = json.loads(request.body)
        operation = body.get("operation")
        resource_id = body.get("resourceId")
        volume_id = body.get("volumeId")
        category = body.get("categorySlug")
        multimask_geojson = body.get('multimaskGeoJSON')
        update_list = body.get('updateList', [])

        response = {
            "status": "",
            "message": ""
        }

        if operation == "update":
            for resource_id, category in update_list:
                map = get_object_or_404(Map, pk=volume_id)
                layer = get_object_or_404(Layer, pk=resource_id)

                try:
                    layerset = map.get_layerset(category, create=True)
                    layer.set_layerset(layerset)
                    response['status'] = "success"
                    response['message'] = f"{resource_id} added to {category} layerset"

                except Exception as e:
                    logger.error(e)
                    response['status'] = "fail"
                    response['message'] = str(e)

        if operation == "check-for-existing-mask":

            r = get_object_or_404(Layer, pk=resource_id)

            if r.layerset:
                if not r.layerset.category.slug == category:
                    if r.layerset.multimask and r.slug in r.layerset.multimask:
                        response['status'] = "fail"
                        response['message'] = f"Layer already in {r.layerset.category} multimask."
                        return JsonResponse(response)

            response['status'] = "success"
            return JsonResponse(response)

        if operation == "set-mask":

            try:
                layerset = LayerSet.objects.get(map_id=volume_id, category__slug=category)
                errors = layerset.update_multimask_from_geojson(multimask_geojson)
                if errors:
                    response["status"] = "fail"
                    response["message"] = errors
                else:
                    response["status"] = "success"
            except LayerSet.DoesNotExist:
                response["status"] = "fail"
                response["message"] = f"can't find this layerset: map_id={volume_id}, category={category}"


        return JsonResponse(response)
