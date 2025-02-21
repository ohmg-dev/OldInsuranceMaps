import json
import logging

from natsort import natsorted

from django.contrib.auth import get_user_model
from django.http import JsonResponse, Http404
from django.shortcuts import render, get_object_or_404
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

from ohmg.core.http import generate_ohmg_context
from ohmg.core.models import (
    Map,
    Document,
    Region,
    Layer,
    LayerSet,
    LayerSetCategory,
)
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
    load_document_file_as_task,
)

from .http import (
    validate_post_request,
    JsonResponseSuccess,
    JsonResponseFail,
    JsonResponseNotFound,
)

logger = logging.getLogger(__name__)


def test_map_access(user, map):
    if map.access_level == "none" and not user.is_superuser:
        raise Http404
    elif map.access_level == "restricted":
        if (
            user not in map.user_access.all()
            and len([i for i in user.groups.all() if i in map.group_access.all()]) == 0
            and not user.is_superuser
        ):
            raise Http404


class MapView(View):
    @time_this
    def get(self, request, identifier):
        map = get_object_or_404(Map.objects.prefetch_related(), pk=identifier)

        test_map_access(request.user, map)

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
    @method_decorator(validate_post_request(operations=["load-documents", "refresh-lookups"]))
    def post(self, request, identifier):
        body = json.loads(request.body)
        operation = body.get("operation")

        if operation == "load-documents":
            map = Map.objects.get(pk=identifier)
            load_map_documents_as_task.apply_async((identifier, request.user.username))
            map_json = MapFullSchema.from_orm(map).dict()
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
        test_map_access(request.user, resource.map)
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
    @method_decorator(validate_post_request(operations=["unprepare", "load-file"]))
    def post(self, request, pk):
        from ohmg.georeference.models import PrepSession

        document = self._get_object(pk)
        if document is None:
            return JsonResponseNotFound()

        body = json.loads(request.body)
        operation = body.get("operation")

        if operation == "unprepare":
            sesh = PrepSession.objects.get(doc2=document)
            result = sesh.undo()
            if result["success"]:
                return JsonResponseSuccess(result["message"])
            else:
                return JsonResponseFail(result["message"])

        if operation == "load-file":
            load_document_file_as_task.apply_async((pk, request.user.username))
            return JsonResponseSuccess(f"file load started for document {pk}")


class RegionView(GenericResourceView):
    model = Region

    @method_decorator(login_required)
    @method_decorator(
        validate_post_request(
            operations=["set-category"],
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
