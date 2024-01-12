import logging

from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.views import View
from django.middleware import csrf
from django.urls import reverse

from ohmg.georeference.models import (
    Layer,
    Document,
    ItemBase,
)

from ohmg.loc_insurancemaps.models import find_volume

logger = logging.getLogger(__name__)

class ResourceView(View):

    def get(self, request, pk):

        resource = get_object_or_404(ItemBase, pk=pk)
        if resource.type == 'document':
            resource = Document.objects.get(pk=pk)
        elif resource.type == 'layer':
            resource = Layer.objects.get(pk=pk)

        split_summary = resource.get_split_summary()
        georeference_summary = resource.get_georeference_summary()
        sessions_json = resource.get_sessions(serialize=True)
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
                    'USER_AUTHENTICATED': request.user.is_authenticated,
                    'USER_STAFF': request.user.is_staff,
                    "SPLIT_SUMMARY": split_summary,
                    "GEOREFERENCE_SUMMARY": georeference_summary,
                    "SESSION_HISTORY": sessions_json,
                    "MAPBOX_API_KEY": settings.MAPBOX_API_TOKEN,
                    "OHMG_API_KEY": settings.OHMG_API_KEY,
                    "SESSION_API_URL": reverse("api-beta:session_list"),
                    "TITILER_HOST": settings.TITILER_HOST,
                }
            }
        )
