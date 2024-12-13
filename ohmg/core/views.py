import json
import logging
from datetime import datetime

from natsort import natsorted

from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

from ohmg.georeference.models import LayerSetCategory
from ohmg.core.context_processors import generate_ohmg_context
from ohmg.core.models import Map, Document, Region, Layer
from ohmg.core.utils import time_this
from ohmg.core.api.schemas import (
    MapFullSchema,
    MapResourcesSchema,
    PlaceFullSchema,
    LayerSetSchema,
    ResourceFullSchema,
)
from ohmg.core.tasks import (
    load_map_documents_as_task,
)
from ohmg.georeference.tasks import (
    run_preparation_session,
)

from .http import (
    validate_post_request,
    JsonResponseSuccess,
    JsonResponseFail,
    JsonResponseNotFound,
)

logger = logging.getLogger(__name__)


class MapView(View):
    @time_this
    def get(self, request, identifier):
        map = get_object_or_404(Map.objects.prefetch_related(), pk=identifier)
        map_json = MapFullSchema.from_orm(map).dict()

        session_summary = map.get_session_summary()

        locale_json = PlaceFullSchema.from_orm(map.get_locale()).dict()

        layersets = [LayerSetSchema.from_orm(i).dict() for i in map.layerset_set.all()]
        layerset_categories = list(LayerSetCategory.objects.all().values("slug", "display_name"))

        users = get_user_model().objects.all()
        user_filter_list = natsorted(
            [{"title": i, "id": i} for i in users.values_list("username", flat=True)],
            key=lambda k: k["id"],
        )

        context_dict = {
            "svelte_params": {
                "CONTEXT": generate_ohmg_context(request),
                "MAP": map_json,
                "LOCALE": locale_json,
                "SESSION_SUMMARY": session_summary,
                "LAYERSETS": layersets,
                "LAYERSET_CATEGORIES": layerset_categories,
                "userFilterItems": user_filter_list,
            }
        }

        return render(request, "content/map.html", context=context_dict)

    @method_decorator(login_required)
    def post(self, request, identifier):
        body = json.loads(request.body)
        operation = body.get("operation", None)

        if operation == "initialize":
            map = Map.objects.get(pk=identifier)
            if map.loaded_by is None:
                map.loaded_by = request.user
                map.load_date = datetime.now()
                map.save(update_fields=["loaded_by", "load_date"])
            load_map_documents_as_task.apply_async((identifier,))
            map_json = MapFullSchema.from_orm(map).dict()
            map_json["status"] = "initializing..."
            return JsonResponse(map_json)

        elif operation == "refresh-lookups":
            map = get_object_or_404(Map.objects.prefetch_related(), pk=identifier)
            map.update_item_lookup()
            map_json = MapFullSchema.from_orm(map).dict()
            return JsonResponse(map_json)


class GenericResourceView(View):
    model = None
    post_operations = []

    def _get_object(self, pk):
        try:
            return self.model.objects.get(pk=pk)
        except self.model.DoesNotExist:
            return None

    @time_this
    def get(self, request, pk):
        resource = get_object_or_404(self.model, pk=pk)
        return render(
            request,
            "content/resource.html",
            context={
                "resource_params": {
                    "CONTEXT": generate_ohmg_context(request),
                    "MAP": MapResourcesSchema.from_orm(resource.map).dict(),
                    "LOCALE": PlaceFullSchema.from_orm(resource.map.get_locale()).dict(),
                    "RESOURCE": ResourceFullSchema.from_orm(resource).dict(),
                }
            },
        )


class DocumentView(GenericResourceView):
    model = Document

    @method_decorator(login_required)
    @method_decorator(validate_post_request(operations=["no-split", "split", "unprepare"]))
    def post(self, request, pk):
        from ohmg.georeference.models import PrepSession

        document = self._get_object(pk)
        if document is None:
            return JsonResponseNotFound()

        body = json.loads(request.body)
        operation = body.get("operation")
        payload = body.get("payload")

        sessionid = payload.get("sessionId")
        sesh = None
        if sessionid:
            sesh = PrepSession.objects.get(pk=sessionid)

        if operation in ["split", "no-split"]:
            if Region.objects.filter(document=document).exists():
                return JsonResponseFail(
                    f"This document {document} ({document.pk}) has already been prepared."
                )

        if operation == "no-split":
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

        if operation == "split":
            sesh.data["split_needed"] = True
            sesh.data["cutlines"] = payload.get("lines")
            sesh.save(update_fields=["data"])
            logger.info(f"{sesh.__str__()} | begin run() as task")
            run_preparation_session.apply_async((sesh.pk,))
            return JsonResponse({"success": True})

        if operation == "unprepare":
            sesh = PrepSession.objects.get(doc2=document)
            result = sesh.undo()
            if result["success"]:
                return JsonResponseSuccess(result["message"])
            else:
                return JsonResponseFail(result["message"])


class RegionView(GenericResourceView):
    model = Region

    @method_decorator(login_required)
    @method_decorator(
        validate_post_request(
            operations=["set-category", "georeference"],
        )
    )
    def post(self, request, pk):
        region = self._get_object(pk)
        if region is None:
            return JsonResponseNotFound()

        body = json.loads(request.body)
        operation = body.get("operation")
        payload = body.get("payload")

        if operation == "set-category":
            cat = payload.get("new-category", None)
            if cat == "non-map":
                region.is_map = False
            elif cat == "map":
                region.is_map = True
            else:
                return JsonResponseFail(f"Invalid category for Region: {cat}")
            region.save()
            return JsonResponseSuccess()

        if operation == "georeference":
            # move "submit" operation on ohmg.georeference.views.GeoreferenceView here
            pass


class LayerView(GenericResourceView):
    model = Layer

    @method_decorator(login_required)
    @method_decorator(validate_post_request(operations=["set-layerset", "ungeoreference"]))
    def post(self, request, pk):
        layer = self._get_object(pk)
        if layer is None:
            return JsonResponseNotFound()

        body = json.loads(request.body)
        operation = body.get("operation")
        payload = body.get("payload")

        # typically this is done in bulk with a different endpoint,
        # so this operation may not actually be needed...
        if operation == "set-layerset":
            target_category = payload.get("layerset-category")
            layerset = layer.region.document.map.get_layerset(target_category, create=True)
            try:
                layer.set_layerset(layerset)
                return JsonResponseSuccess(
                    f"Layer {layer.pk} added to {target_category} LayerSet {layerset.pk}"
                )
            except Exception as e:
                logger.error(e)
                return JsonResponseFail(e)

        if operation == "ungeoreference":
            from ohmg.georeference.models import GeorefSession

            sessions = GeorefSession.objects.filter(lyr2=layer)
            sessions.delete()
            layer.region.georeferenced = False
            layer.region.save()
            layer.delete()
            logger.debug((msg := f"Layer {pk} removed through ungeoreference process."))
            return JsonResponseSuccess(msg)
