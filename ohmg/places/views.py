from natsort import natsorted

from django.shortcuts import render
from django.views import View
from django.views.decorators.clickjacking import xframe_options_sameorigin

from ohmg.core.http import generate_ohmg_context
from ohmg.core.models import Map
from ohmg.core.api.schemas import (
    LayerSetSchema,
    MapFullSchema,
)

from ohmg.core.api.schemas import PlaceFullSchema


class PlaceView(View):
    def get(self, request, place):
        place_json = PlaceFullSchema.from_orm(place).dict()
        print(place_json)
        context_dict = {
            "params": {
                "CONTEXT": generate_ohmg_context(request),
                "PAGE_NAME": "place",
                "PARAMS": {
                    "PLACE": place_json,
                },
            },
            "navlinks": [
                {
                    "icon": "camera",
                    "url": place_json["url"],
                    "active": True,
                }
            ],
        }
        return render(request, "places/place.html", context=context_dict)


class Viewer(View):
    @xframe_options_sameorigin
    def get(self, request, place):
        place_data = {}
        maps = []

        place_data = place.serialize()
        for map in Map.objects.filter(locales__id__exact=place.id, hidden=False).prefetch_related():
            map_json = MapFullSchema.from_orm(map).dict()
            ls = map.get_layerset("main-content")
            if ls:
                map_json["main_layerset"] = LayerSetSchema.from_orm(ls).dict()
                maps.append(map_json)

        maps_sorted = natsorted(maps, key=lambda x: x["title"], reverse=True)

        context_dict = {
            "svelte_params": {
                "CONTEXT": generate_ohmg_context(request),
                "PLACE": place_data,
                "MAPS": maps_sorted,
            }
        }
        return render(request, "places/viewer.html", context=context_dict)
