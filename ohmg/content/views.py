import json
import logging
from datetime import datetime

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views import View
from django.middleware import csrf
from django.urls import reverse

from ohmg.georeference.models import (
    Layer,
    Document,
    ItemBase,
)
from ohmg.loc_insurancemaps.models import Volume, find_volume
from ohmg.loc_insurancemaps.tasks import load_docs_as_task
from ohmg.frontend.context_processors import user_info_from_request

logger = logging.getLogger(__name__)


class MapSummary(View):

    def get(self, request, identifier):

        volume = get_object_or_404(Volume, pk=identifier)
        volume_json = volume.serialize(include_session_info=True)

        context_dict = {
            "svelte_params": {
                "TITILER_HOST": settings.TITILER_HOST,
                "VOLUME": volume_json,
                "CSRFTOKEN": csrf.get_token(request),
                "USER": user_info_from_request(request),
                "MAPBOX_API_KEY": settings.MAPBOX_API_TOKEN,
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

        elif operation == "set-index-layers":

            volume = Volume.objects.get(pk=identifier)

            lcat_lookup = body.get("layerCategoryLookup", {})

            for cat in volume.sorted_layers:
                volume.sorted_layers[cat] = [k for k, v in lcat_lookup.items() if v == cat]

            volume.save(update_fields=["sorted_layers"])
            volume_json = volume.serialize(include_session_info=True)
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
                    'REFRESH_URL': None,
                    'RESOURCE': resource_json,
                    'VOLUME': volume_json,
                    'CSRFTOKEN': csrf.get_token(request),
                    "USER": user_info_from_request(request),
                    "SPLIT_SUMMARY": split_summary,
                    "GEOREFERENCE_SUMMARY": georeference_summary,
                    "MAPBOX_API_KEY": settings.MAPBOX_API_TOKEN,
                    "OHMG_API_KEY": settings.OHMG_API_KEY,
                    "SESSION_API_URL": reverse("api-beta:session_list"),
                    "TITILER_HOST": settings.TITILER_HOST,
                }
            }
        )
