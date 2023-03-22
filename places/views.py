import logging

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views import View
from django.views.decorators.clickjacking import xframe_options_sameorigin

from loc_insurancemaps.models import Volume
from places.models import Place

logger = logging.getLogger(__name__)


class PlaceView(View):

    def get(self, request, place_slug):

        f = request.GET.get("f", None)
        p = get_object_or_404(Place, slug=place_slug)
        data = p.serialize()

        if f == "json":
            return JsonResponse(data)

        else:
            context_dict = {
                "svelte_params": {
                    "PLACE": data,
                }
            }
            return render(
                request,
                "place.html",
                context=context_dict
            )


class Viewer(View):

    @xframe_options_sameorigin
    def get(self, request, place_slug):

        place_data = {}
        volumes = []

        p = Place.objects.filter(slug=place_slug)
        if p.count() == 1:
            place = p[0]
        else:
            place = Place.objects.get(slug="louisiana")

        place_data = place.serialize()
        for v in Volume.objects.filter(locale=place).order_by("year","volume_no").reverse():
            volumes.append(v.serialize())

        context_dict = {
            "svelte_params": {
                "PLACE": place_data,
                "VOLUMES": volumes,
                "TITILER_HOST": settings.TITILER_HOST,
                "MAPBOX_API_KEY": settings.MAPBOX_API_TOKEN,
            }
        }
        return render(
            request,
            "viewer.html",
            context=context_dict
        )