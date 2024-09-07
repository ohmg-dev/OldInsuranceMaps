import json
import logging
from datetime import datetime

from django.db.models import F
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views import View

from ohmg.georeference.models import (
    LayerV1,
    Document,
    ItemBase,
    LayerSetCategory,
)
from ohmg.core.context_processors import generate_ohmg_context
from ohmg.core.models import (
    Map,
)
from ohmg.core.utils import time_this
from ohmg.core.api.schemas import (
    MapFullSchema,
    PlaceFullSchema,
    LayerSetSchema,
    SessionLockSchema,
)
from ohmg.georeference.models import SessionLock
from ohmg.loc_insurancemaps.models import Volume, find_volume
from ohmg.loc_insurancemaps.tasks import load_docs_as_task, load_map_documents_as_task

logger = logging.getLogger(__name__)


class PageView(View):

    def get(self, request, page):

        context_dict = {
            "params": {
                "PAGE_TITLE": page.title,
                "PAGE_NAME": 'markdown-page',
                "PARAMS": {
                    "HEADER": page.title,
                    # downstream SvelteMarkdown requires this variable to be `source`
                    "source": page.content,
                }
            }
        }

        return render(
            request,
            "index.html",
            context=context_dict
        )


class MapSummary(View):

    @time_this
    def get(self, request, identifier):

        map = get_object_or_404(Map.objects.prefetch_related(), pk=identifier)
        map_json = MapFullSchema.from_orm(map).dict()

        session_summary = map.get_session_summary()

        locale_json = PlaceFullSchema.from_orm(map.get_locale()).dict()

        annotation_sets = [LayerSetSchema.from_orm(i).dict() for i in map.layerset_set.all()]
        annotation_set_options = list(LayerSetCategory.objects.filter(is_geospatial=True).values("slug", "display_name"))

        context_dict = {
            "svelte_params": {
                "CONTEXT": generate_ohmg_context(request),
                "MAP": map_json,
                "LOCALE": locale_json,
                "SESSION_SUMMARY": session_summary,
                "ANNOTATION_SETS": annotation_sets,
                "ANNOTATION_SET_OPTIONS": annotation_set_options,
            }
        }

        return render(
            request,
            "content/map.html",
            context=context_dict
        )

    def post(self, request, identifier):

        body = json.loads(request.body)
        operation = body.get("operation", None)

        if operation == "initialize":
            volume = Volume.objects.get(pk=identifier)
            if volume.loaded_by is None:
                volume.loaded_by = request.user
                volume.load_date = datetime.now()
                volume.save(update_fields=["loaded_by", "load_date"])
            map = Map.objects.get(pk=identifier)
            if map.loaded_by is None:
                map.loaded_by = request.user
                map.load_date = datetime.now()
                map.save(update_fields=["loaded_by", "load_date"])
            load_map_documents_as_task.apply_async((identifier,),
                link=load_docs_as_task.s()
            )
            map_json = MapFullSchema.from_orm(map).dict()
            map_json["status"] = "initializing..."
            return JsonResponse(map_json)

        elif operation == "refresh-lookups":
            map = get_object_or_404(Map.objects.prefetch_related(), pk=identifier)
            map.update_item_lookup()
            map_json = MapFullSchema.from_orm(map).dict()
            return JsonResponse(map_json)


class VirtualResourceView(View):

    def get(self, request, pk):

        resource = get_object_or_404(ItemBase, pk=pk)
        if resource.type == 'document':
            resource = Document.objects.get(pk=pk)
        elif resource.type == 'layer':
            resource = LayerV1.objects.get(pk=pk)

        split_summary = resource.get_split_summary()
        georeference_summary = resource.get_georeference_summary()
        resource_json = resource.serialize()

        volume = find_volume(resource)
        volume_json = None
        if volume is not None:
            volume_json = volume.serialize()

        return render(
            request,
            "content/resource.html",
            context={
                'resource_params': {
                    "CONTEXT": generate_ohmg_context(request),
                    'RESOURCE': resource_json,
                    'VOLUME': volume_json,
                    "SPLIT_SUMMARY": split_summary,
                    "GEOREFERENCE_SUMMARY": georeference_summary,
                }
            }
        )
