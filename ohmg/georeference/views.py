import os
import json
from datetime import datetime
import logging

from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.views import View
from django.http import JsonResponse
from django.utils.decorators import method_decorator

from ohmg.core.http import (
    JsonResponseSuccess,
    JsonResponseFail,
    JsonResponseBadRequest,
    JsonResponseNotFound,
    validate_post_request,
    generate_ohmg_context,
)
from ohmg.core.utils import time_this
from ohmg.georeference.tasks import (
    run_georeference_session,
)
from ohmg.georeference.models import (
    SessionBase,
    PrepSession,
    GeorefSession,
)
from ohmg.core.api.schemas import (
    DocumentFullSchema,
    LayerSetSchema,
    MapFullSchema,
    RegionFullSchema,
)
from ohmg.core.models import (
    Map,
    Document,
    Region,
    Layer,
    LayerSet,
)
from ohmg.georeference.georeferencer import Georeferencer
from ohmg.georeference.splitter import Splitter
from ohmg.georeference.tasks import delete_preview_vrt

logger = logging.getLogger(__name__)


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
            session = PrepSession.objects.create(user=request.user, doc2=document)
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
            context={"split_params": split_params},
        )

    # @method_decorator(validate_post_request(operations=[]))
    def post(self, request, docid):
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
                logger.warning(
                    f"can't find PrepSession ({sesh_id}), expected for Document {document.pk}"
                )
                return JsonResponse({"success": False, "message": "no session found"})

        if operation == "preview":
            s = Splitter(image_file=document.file.path)
            divisions = s.generate_divisions(cutlines)
            return JsonResponse({"success": True, "divisions": divisions})

        elif operation == "cancel":
            if sesh.stage != "input":
                msg = "can't cancel session that is past the input stage"
                logger.warning(f"{sesh.__str__()} | {msg}")
                return JsonResponse({"success": True, "message": msg})
            sesh.delete()
            return JsonResponse({"success": True})

        else:
            return JsonResponseBadRequest()


class GeoreferenceView(View):
    def get(self, request, docid):
        """
        Returns the georeferencing interface for this document.
        """

        region = get_object_or_404(Region, pk=docid)

        # if the region is not currently locked and there is a logged in user,
        # create a new session
        if not region.lock and request.user.is_authenticated:
            session = GeorefSession.objects.create(
                reg2=region,
                user=request.user,
            )
            if hasattr(region, "layer"):
                session.lyr2 = region.layer
            session.start()

        region_json = RegionFullSchema.from_orm(region).dict()

        map_json = MapFullSchema.from_orm(region.map).dict()

        main_layerset = None
        mc = region.document.map.get_layerset("main-content")
        if mc:
            main_layerset = LayerSetSchema.from_orm(mc).dict()
        keymap_layerset = None
        akm = region.document.map.get_layerset("key-map")
        if akm:
            keymap_layerset = LayerSetSchema.from_orm(akm).dict()

        georeference_params = {
            "CONTEXT": generate_ohmg_context(request),
            "REGION": region_json,
            "MAP": map_json,
            "MAIN_LAYERSET": main_layerset,
            "KEYMAP_LAYERSET": keymap_layerset,
        }

        return render(
            request,
            "georeference/georeference.html",
            context={
                "georeference_params": georeference_params,
            },
        )

    @method_decorator(validate_post_request(operations=["preview", "submit", "cancel"]))
    def post(self, request, docid):
        """
        Runs the georeferencing process for this document.
        """

        region = get_object_or_404(Region, pk=docid)

        body = json.loads(request.body)
        operation = body.get("operation")
        payload = body.get("payload")

        gcp_geojson = payload.get("gcp_geojson", {})
        transformation = payload.get("transformation", "poly1")
        projection = payload.get("projection", "EPSG:3857")
        sesh_id = payload.get("sesh_id", None)
        cleanup_preview = payload.get("cleanup_preview", None)

        def _generate_preview_id(request, sesh_id):
            try:
                ip_val = request.META.get("REMOTE_ADDR", "0.0.0.0.").replace(".", "-")
            except Exception as e:
                logger.warning(e)
                ip_val = "000000000"

            sesh_val = 0
            if sesh_id:
                sesh_val = sesh_id

            return f"{ip_val}-{sesh_val}-{int(datetime.now().timestamp())}"

        def _cleanup_preview(region, previous_url):
            """Run this deletion through celery, so that it doesn't delay
            the return of whatever function called it."""
            if previous_url:
                delete_preview_vrt.delay(region.file.path, previous_url)

        def _get_georef_session(sesh_id):
            try:
                sesh = GeorefSession.objects.get(pk=sesh_id)
            except GeorefSession.DoesNotExist:
                sesh = None
            return sesh

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
                out_path_relative = os.path.join(
                    os.path.dirname(region.file.url), os.path.basename(out_path)
                )
                preview_url = settings.MEDIA_HOST.rstrip("/") + out_path_relative
                _cleanup_preview(region, cleanup_preview)
                return JsonResponseSuccess("all good", {"preview_url": preview_url})
            except Exception as e:
                logger.error(e)
                return JsonResponseFail(str(e))

        elif operation == "submit":
            sesh = _get_georef_session(sesh_id)
            if sesh:
                # ultimately, should be putting the whole "EPSG:3857"
                # in the session data, but for now stick with just the number
                # see models.sessions.py line 510
                epsg_code = int(projection.split(":")[1])
                sesh.data["epsg"] = epsg_code
                sesh.data["gcps"] = gcp_geojson
                sesh.data["transformation"] = transformation
                sesh.save(update_fields=["data"])
                logger.info(f"{sesh.__str__()} | begin run() as task")
                run_georeference_session.apply_async((sesh.pk,))

                _cleanup_preview(region, cleanup_preview)
                return JsonResponseSuccess()

            else:
                return JsonResponseNotFound(
                    f"session {sesh_id} not found: submit must be called with existing session"
                )

        elif operation == "cancel":
            sesh = _get_georef_session(sesh_id)
            if sesh:
                if sesh.stage != "input":
                    msg = "can't cancel session that is past the input stage"
                    logger.warning(f"{sesh.__str__()} | {msg}")
                    return JsonResponseFail(msg)

                sesh.delete()

            _cleanup_preview(region, cleanup_preview)
            return JsonResponseSuccess()

        else:
            return JsonResponseBadRequest()


class LayerSetView(View):
    @method_decorator(
        validate_post_request(
            operations=["bulk-classify-layers", "check-for-existing-mask", "set-mask"]
        )
    )
    def post(self, request):
        body = json.loads(request.body)
        operation = body.get("operation")
        payload = body.get("payload", {})

        if operation == "bulk-classify-layers":
            errors = []
            for lyr_id, cat in payload.get("update-list"):
                map = get_object_or_404(Map, pk=payload.get("map-id"))
                layer = get_object_or_404(Layer, pk=lyr_id)
                try:
                    layerset = map.get_layerset(cat, create=True)
                    layer.set_layerset(layerset)
                except Exception as e:
                    logger.error(e)
                    errors.append(str(e))

            if errors:
                return JsonResponseFail("; ".join(errors))
            else:
                return JsonResponseSuccess("Layers classified successfully.")

        if operation == "check-for-existing-mask":
            r = get_object_or_404(Layer, pk=payload.get("resource-id"))

            if r.layerset2:
                if not r.layerset2.category.slug == payload.get("category"):
                    if r.layerset2.multimask and r.slug in r.layerset2.multimask:
                        return JsonResponseFail(
                            f"Layer already in {r.layerset2.category} multimask.",
                            payload=payload,
                        )

            return JsonResponseSuccess(payload=payload)

        if operation == "set-mask":
            try:
                layerset = LayerSet.objects.get(
                    map_id=payload["map-id"], category__slug=payload["category"]
                )
                errors = layerset.update_multimask_from_geojson(payload["multimask-geojson"])
                print(errors)
                if errors:
                    return JsonResponseFail("; ".join([f"\n-- {i[0]}: {i[1]}" for i in errors]))
                else:
                    return JsonResponseSuccess()
            except LayerSet.DoesNotExist:
                return JsonResponseNotFound()


class SessionView(View):
    def _get_session(self, sessionid):
        try:
            bs = SessionBase.objects.get(pk=sessionid)
            if bs.type == "p":
                return PrepSession.objects.get(pk=sessionid)
            elif bs.type == "g":
                return GeorefSession.objects.get(pk=sessionid)
        except (
            SessionBase.DoesNotExist,
            PrepSession.DoesNotExist,
            GeorefSession.DoesNotExist,
        ):
            return JsonResponseNotFound()

    @method_decorator(validate_post_request(operations=["undo", "cancel", "extend"]))
    def post(self, request, sessionid):
        session = self._get_session(sessionid)
        body = json.loads(request.body)
        operation = body.get("operation")

        ## currently this operation is not used, in favor of document/<pk> 'unprepare'
        if operation == "undo":
            try:
                session.undo()
            except Exception as e:
                return JsonResponseFail(e)
            return JsonResponseSuccess()

        if operation == "extend":
            try:
                session.extend_locks()
            except Exception as e:
                return JsonResponseFail(e)
            return JsonResponseSuccess()
