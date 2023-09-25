import re
import logging

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views import View
from django.views.decorators.clickjacking import xframe_options_sameorigin

from ohmg.loc_insurancemaps.models import Volume
from ohmg.places.models import Place

logger = logging.getLogger(__name__)

def mobile(request):
    """Return True if the request comes from a mobile device."""

    MOBILE_AGENT_RE=re.compile(r".*(iphone|mobile|androidtouch)",re.IGNORECASE)

    if MOBILE_AGENT_RE.match(request.META['HTTP_USER_AGENT']):
        return True
    else:
        return False


class PlaceView(View):

    def get(self, request, place_slug):

        f = request.GET.get("f", None)
        p = get_object_or_404(Place, slug=place_slug)
        data = p.serialize()

        if f == "json":
            return JsonResponse(data)

        else:
            context_dict = {
                "params": {
                    "PAGE_NAME": 'place',
                    "PARAMS": {
                        "PLACE": data,
                    }
                }
            }
            return render(
                request,
                "index.html",
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
        for v in Volume.objects.filter(locales__id__exact=place.id).order_by("year","volume_no").reverse():
            volumes.append(v.serialize())

        context_dict = {
            "svelte_params": {
                "PLACE": place_data,
                "VOLUMES": volumes,
                "TITILER_HOST": settings.TITILER_HOST,
                "MAPBOX_API_KEY": settings.MAPBOX_API_TOKEN,
                "ON_MOBILE": mobile(request),
            }
        }
        return render(
            request,
            "viewer.html",
            context=context_dict
        )
