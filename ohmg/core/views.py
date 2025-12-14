import json
import logging
from urllib.parse import quote

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.gis.geos import Polygon
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import HttpResponse, get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from natsort import natsorted
from slugify import slugify

from ohmg.accounts.models import User
from ohmg.api.schemas import (
    LayerSetSchema,
    MapFullSchema,
    MapResourcesSchema,
    MapUserSchema,
    PlaceFullSchema,
    ResourceFullSchema,
)
from ohmg.conf.http import (
    JsonResponseFail,
    JsonResponseNotFound,
    JsonResponseSuccess,
    generate_ohmg_context,
    validate_post_request,
)
from ohmg.georeference.models import GCP, SessionBase

from .exporters.qlr import generate_qlr_content
from .models import (
    Document,
    Layer,
    LayerSet,
    LayerSetCategory,
    Map,
    Region,
    RegionCategory,
)
from .storages import get_file_url
from .tasks import (
    load_document_file_as_task,
    load_map_documents_as_task,
)
from .utils.performance import time_this_function

logger = logging.getLogger(__name__)


def test_map_access(user, map):
    access_allowed = True
    if map.access_level == "none" and not user.is_superuser:
        access_allowed = False
    elif map.access_level == "restricted":
        if (
            user not in map.user_access.all()
            and len([i for i in user.groups.all() if i in map.group_access.all()]) == 0
            and not user.is_superuser
        ):
            access_allowed = False
    return access_allowed


class MapListView(View):
    def get(self, request):
        context_dict = {
            "MAPS_PARAMS": {
                "CONTEXT": generate_ohmg_context(request),
            }
        }
        return render(request, "core/maps.html", context=context_dict)


class MapView(View):
    @time_this_function
    def get(self, request, identifier):
        map = get_object_or_404(Map.objects.prefetch_related(), pk=identifier)

        if not test_map_access(request.user, map):
            return HttpResponse("Unauthorized: You do not have access to this item.", status=401)

        map_json = MapFullSchema.from_orm(map).dict()

        session_summary = map.get_session_summary()

        locale_json = PlaceFullSchema.from_orm(map.get_locale()).dict()

        layersets = [LayerSetSchema.from_orm(i).dict() for i in map.layerset_set.all()]
        layerset_categories = list(LayerSetCategory.objects.all().values("slug", "display_name"))

        context_dict = {
            "svelte_params": {
                "CONTEXT": generate_ohmg_context(request),
                "MAP": map_json,
                "LOCALE": locale_json,
                "SESSION_SUMMARY": session_summary,
                "LAYERSETS": layersets,
                "LAYERSET_CATEGORIES": layerset_categories,
            },
            "navlinks": [
                {
                    "icon": "camera",
                    "url": map_json["urls"]["viewer"],
                    "active": True,
                }
            ],
        }

        return render(request, "core/map.html", context=context_dict)

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


class MapContributorsView(View):
    def get(self, request, identifier):
        sort = request.GET.get("sort")
        sortby = request.GET.get("sortby")
        map = get_object_or_404(Map.objects.prefetch_related(), pk=identifier)
        sessions = SessionBase.objects.filter(map=map)
        users_by_type = sessions.values_list("user", "type")
        user_ids = set([i[0] for i in users_by_type])
        users_json = []
        for u in User.objects.filter(pk__in=user_ids):
            user_json = MapUserSchema.from_orm(u).dict()
            user_json["psesh_ct"] = len([i for i in users_by_type if i[0] == u.pk and i[1] == "p"])
            user_json["gsesh_ct"] = len([i for i in users_by_type if i[0] == u.pk and i[1] == "g"])
            user_json["gcp_ct"] = GCP.objects.filter(
                created_by=u, gcp_group__region2__in=map.regions.all()
            ).count()
            users_json.append(user_json)
        if sortby:
            users_json = natsorted(
                users_json,
                key=lambda x: x[sortby].lower() if isinstance(x[sortby], str) else x[sortby],
                reverse=sort == "des",
            )
        return JsonResponse({"items": users_json})


class GenericResourceView(View):
    model = None
    post_operations = []

    def _get_object(self, pk):
        try:
            return self.model.objects.get(pk=pk)
        except self.model.DoesNotExist:
            return None

    @time_this_function
    def get(self, request, pk):
        resource = get_object_or_404(self.model, pk=pk)
        if not test_map_access(request.user, resource.map):
            return HttpResponse("Unauthorized: You do not have access to this item.", status=401)

        map_json = MapResourcesSchema.from_orm(resource.map).dict()
        place_json = PlaceFullSchema.from_orm(resource.map.get_locale()).dict()
        resource_json = ResourceFullSchema.from_orm(resource).dict()

        layer = None
        if self.model is Layer:
            layer = resource
        elif self.model is Region and resource.georeferenced:
            layer = resource.layer

        viewer_url = None
        if layer:
            centroid = Polygon.from_bbox(layer.extent).centroid
            viewer_url = f"/viewer/{place_json['slug']}/?${map_json['identifier']}=100#/center/{centroid.x},{centroid.y}/zoom/18"

        navlinks = [
            {
                "icon": "volume",
                "url": f"/map/{resource.map.pk}",
                "active": True,
            },
            {
                "icon": "camera",
                "url": viewer_url,
                "active": viewer_url is not None,
            },
        ]
        if self.model is not Document:
            navlinks.insert(
                0,
                {
                    "icon": "document",
                    "url": f"/document/{resource.document.pk if self.model is Region else resource.region.document.pk}",
                    "active": True,
                },
            )
        return render(
            request,
            "core/resource.html",
            context={
                "resource_params": {
                    "CONTEXT": generate_ohmg_context(request),
                    "MAP": map_json,
                    "LOCALE": place_json,
                    "RESOURCE": resource_json,
                },
                "lead_icon": "document" if self.model is Document else "layer",
                "navlinks": navlinks,
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
            operations=["set-category", "set-skip"],
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
            try:
                cat_obj = RegionCategory.objects.get(slug=cat)
            except RegionCategory.DoesNotExist:
                return JsonResponseFail(f"Invalid category for Region: {cat}")
            region.category = cat_obj
            region.save()
            return JsonResponseSuccess()

        if operation == "set-skip":
            skipped = payload.get("skipped", False)
            region.skipped = skipped
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


class ResourceDerivativeView(View):
    def get(self, request, pk, derivative, resource=""):
        if resource == "layer":
            layer = get_object_or_404(Layer, pk=pk)
            region = layer.region
            if not test_map_access(request.user, layer.map):
                return HttpResponse(
                    "Unauthorized: You do not have access to this item.", status=401
                )

        elif resource == "region":
            region = get_object_or_404(Region, pk=pk)
            layer = region.layer if hasattr(region, "layer") else None
            if not test_map_access(request.user, region.map):
                return HttpResponse(
                    "Unauthorized: You do not have access to this item.", status=401
                )
        else:
            raise Http404

        raw = request.GET.get("raw", "false")

        region_derivatives = ["img"]
        layer_derivatives = ["qlr", "cog", "services", "tilejson", "ohm"]

        ## these are derivatives from the region
        if derivative in region_derivatives:
            if not region:
                raise Http404

            if derivative == "img":
                return redirect(get_file_url(region))

        ## these derivatives require a layer instance
        elif derivative in layer_derivatives:
            if not layer:
                raise Http404

            if derivative == "qlr":
                xml_str = generate_qlr_content(layer)

                filename = slugify(layer.title)

                if raw.lower() == "true":
                    return HttpResponse(xml_str, content_type="text/xml")

                response = FileResponse(xml_str, content_type="text/xml")
                response["Content-Length"] = len(xml_str)
                response["Content-Disposition"] = f'attachment; filename="{filename}.qlr"'
                return response

            if derivative == "cog":
                return redirect(get_file_url(layer))

            if derivative == "tilejson":
                if layer.tilejson:
                    return JsonResponse(layer.tilejson)
                else:
                    raise Http404

            if derivative == "ohm":
                file_url_encoded = quote(get_file_url(layer), safe="")
                xyz_base = (
                    f"{settings.TITILER_HOST}/cog/tiles/WebMercatorQuad/{{z}}/{{x}}/{{y}}.png?"
                )
                xyz_url_encoded = quote(f"{xyz_base}&url={file_url_encoded}", safe="")
                lon, lat = layer.centroid
                u = f"https://www.openhistoricalmap.org/edit#map=16/{lat}/{lon}&background=custom:{xyz_url_encoded}"
                return redirect(u)

            if derivative == "services":
                file_url_encoded = quote(get_file_url(layer), safe="")
                xyz_base = (
                    f"{settings.TITILER_HOST}/cog/tiles/WebMercatorQuad/{{z}}/{{x}}/{{y}}.png?"
                )
                return JsonResponse(
                    {
                        "xyz": f"{xyz_base}&url={file_url_encoded}",
                        "wms": f"{settings.TITILER_HOST}/cog/wms/?LAYERS={file_url_encoded}&VERSION=1.1.1",
                        "tilejson": f"{settings.SITEURL}layer/{pk}/tilejson",
                    }
                )

        else:
            raise Http404


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
                if errors:
                    return JsonResponseFail("; ".join([f"\n-- {i[0]}: {i[1]}" for i in errors]))
                else:
                    return JsonResponseSuccess()
            except LayerSet.DoesNotExist:
                return JsonResponseNotFound()


class LayersetDerivativeView(View):
    def get(self, request, mapid, category, derivative):
        map = get_object_or_404(Map.objects.prefetch_related(), pk=mapid)

        if not test_map_access(request.user, map):
            return HttpResponse("Unauthorized: You do not have access to this item.", status=401)

        layerset = map.get_layerset(category)
        if not layerset:
            raise Http404

        if not layerset.mosaic_geotiff:
            raise Http404

        raw = request.GET.get("raw", "false")

        if derivative == "tilejson" and layerset.tilejson:
            return JsonResponse(layerset.tilejson)

        elif derivative == "qlr":
            xml_str = generate_qlr_content(layerset)
            filename = slugify(str(layerset))

            if raw.lower() == "true":
                return HttpResponse(xml_str, content_type="text/xml")

            response = FileResponse(xml_str, content_type="text/xml")
            response["Content-Length"] = len(xml_str)
            response["Content-Disposition"] = f'attachment; filename="{filename}.qlr"'
            return response

        elif derivative == "ohm":
            file_url_encoded = quote(get_file_url(layerset, "mosaic_geotiff"), safe="")
            xyz_base = f"{settings.TITILER_HOST}/cog/tiles/WebMercatorQuad/{{z}}/{{x}}/{{y}}.png?"
            xyz_url_encoded = quote(f"{xyz_base}&url={file_url_encoded}", safe="")
            lon, lat = layerset.centroid
            u = f"https://www.openhistoricalmap.org/edit#map=16/{lat}/{lon}&background=custom:{xyz_url_encoded}"
            return redirect(u)

        elif derivative == "cog":
            return redirect(get_file_url(layerset, "mosaic_geotiff"))

        elif derivative == "services":
            file_url_encoded = quote(get_file_url(layerset, "mosaic_geotiff"), safe="")
            xyz_base = f"{settings.TITILER_HOST}/cog/tiles/WebMercatorQuad/{{z}}/{{x}}/{{y}}.png?"
            return JsonResponse(
                {
                    "xyz": f"{xyz_base}&url={file_url_encoded}",
                    "wms": f"{settings.TITILER_HOST}/cog/wms/?LAYERS={file_url_encoded}&VERSION=1.1.1",
                    "tilejson": f"{settings.SITEURL}map/{mapid}/{category}/tilejson",
                }
            )

        else:
            raise Http404
