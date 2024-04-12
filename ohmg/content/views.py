import json
import logging
from datetime import datetime

from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views import View

from ohmg.georeference.models import (
    Layer,
    Document,
    ItemBase,
    SetCategory,
)
from ohmg.context_processors import generate_ohmg_context
from ohmg.georeference.schemas import AnnotationSetSchema
from ohmg.loc_insurancemaps.models import Volume, find_volume
from ohmg.loc_insurancemaps.tasks import load_docs_as_task

logger = logging.getLogger(__name__)


class MapSummary(View):

    def get(self, request, identifier):

        volume = get_object_or_404(Volume, pk=identifier)
        volume_json = volume.serialize(include_session_info=True)

        annotation_sets = [AnnotationSetSchema.from_orm(i).dict() for i in volume.get_annotation_sets()]
        annotation_set_options = list(SetCategory.objects.filter(is_geospatial=True).values("slug", "display_name"))

        context_dict = {
            "svelte_params": {
                "CONTEXT": generate_ohmg_context(request),
                "VOLUME": volume_json,
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
            load_docs_as_task.delay(identifier)
            volume_json = volume.serialize(include_session_info=True)
            volume_json["status"] = "initializing..."

            return JsonResponse(volume_json)

        elif operation == "refresh":
            volume = Volume.objects.get(pk=identifier)
            volume_json = volume.serialize(include_session_info=True)
            return JsonResponse(volume_json)

        elif operation == "refresh-lookups":
            volume = Volume.objects.get(pk=identifier)
            volume.refresh_lookups()
            volume_json = volume.serialize(include_session_info=True)
            return JsonResponse(volume_json)


class VirtualResourceView(View):

    def get(self, request, pk):

        resource = get_object_or_404(ItemBase, pk=pk)
        if resource.type == 'document':
            resource = Document.objects.get(pk=pk)
        elif resource.type == 'layer':
            resource = Layer.objects.get(pk=pk)

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
