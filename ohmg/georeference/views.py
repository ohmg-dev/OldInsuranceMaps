import json
from uuid import uuid4
import logging

from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.views import View
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
    Document,
    Region,
)
from ohmg.georeference.tasks import (
    run_preparation_session,
    run_georeference_session,
    delete_preview_vrts,
)
from ohmg.georeference.georeferencer import Georeferencer
from ohmg.georeference.splitter import Splitter

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
            context={
                "split_params": split_params,
                "navlinks": [{"icon": "volume", "url": f"/map/{document.map.pk}", "active": True}],
            },
        )

    @method_decorator(
        validate_post_request(
            operations=["preview", "no-split", "bulk-no-split", "split", "cancel"]
        )
    )
    def post(self, request, docid=None):
        if docid:
            document = get_object_or_404(Document, pk=docid)

        body = json.loads(request.body)
        operation = body.get("operation")
        payload = body.get("payload", {})

        cutlines = payload.get("lines")
        sesh_id = payload.get("sessionId", None)
        bulk_no_split_ids = payload.get("bulkNoSplitIds", [])

        sesh = None
        if sesh_id is not None:
            try:
                sesh = PrepSession.objects.get(pk=sesh_id)
            except PrepSession.DoesNotExist:
                msg = f"can't find PrepSession ({sesh_id}), expected for Document {document.pk}"
                logger.warning(msg)
                return JsonResponseNotFound(msg)

        if operation == "preview":
            s = Splitter(image_file=document.file)
            divisions = s.generate_divisions(cutlines)
            return JsonResponseSuccess(
                "ok",
                {
                    "divisions": divisions,
                },
            )

        elif operation == "no-split":
            # sesh could be None if this post has been made directly from an overview page,
            # not from the split interface where a session will have already been made.
            if sesh is None:
                sesh = PrepSession.objects.create(
                    doc2=document,
                    user=request.user,
                    user_input_duration=0,
                )
                sesh.start()

            sesh.data["split_needed"] = False
            sesh.save(update_fields=["data"])

            new_region = sesh.run()[0]
            return JsonResponseSuccess(f"no split, new region created: {new_region.pk}")

        elif operation == "bulk-no-split":
            for docid in bulk_no_split_ids:
                document = Document.objects.get(pk=docid)
                sesh = PrepSession.objects.create(
                    doc2=document,
                    user=request.user,
                    user_input_duration=0,
                )
                sesh.start()

                sesh.data["split_needed"] = False
                sesh.save(update_fields=["data"])
                sesh.run()
            return JsonResponseSuccess("bulk prepare completed successfully")

        elif operation == "split":
            sesh.data["split_needed"] = True
            sesh.data["cutlines"] = cutlines
            sesh.save(update_fields=["data"])
            logger.info(f"{sesh.__str__()} | begin run() as task")
            run_preparation_session.apply_async((sesh.pk,))
            return JsonResponseSuccess()

        elif operation == "cancel":
            if sesh.stage != "input":
                msg = "can't cancel session that is past the input stage"
                logger.warning(f"{sesh.__str__()} | {msg}")
                return JsonResponseFail(msg)
            sesh.delete()
            return JsonResponseSuccess()

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
                "navlinks": [
                    {"icon": "volume", "url": f"/map/{region.document.map.pk}", "active": True}
                ],
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
        cleanup_preview_id = payload.get("last_preview_id", None)

        if cleanup_preview_id:
            delete_preview_vrts.delay(cleanup_preview_id)

        def _get_georef_session(sesh_id):
            try:
                sesh = GeorefSession.objects.get(pk=sesh_id)
            except GeorefSession.DoesNotExist:
                sesh = None
            return sesh

        if operation == "preview":
            # prepare Georeferencer object
            g = Georeferencer(
                crs=projection,
                gcps_geojson=gcp_geojson,
                transformation=transformation,
            )
            file_url = settings.MEDIA_HOST.rstrip("/") + region.file.url
            try:
                preview_id = str(uuid4())
                read_vrt, write_vrt = g.make_warped_vrt(file_url, out_name=preview_id)

                return JsonResponseSuccess(
                    "all good", {"preview_url": str(read_vrt), "preview_id": preview_id}
                )
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

            return JsonResponseSuccess()

        else:
            return JsonResponseBadRequest()


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
