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
        place = p.serialize()

        lists = {
            1: {
                "selected": "---",
                "options": [],
            },
            2: {
                "selected": "---",
                "options": [],
            },
            3: {
                "selected": "---",
                "options": [],
            },
            4: {
                "selected": "---",
                "options": [],
            },
            5: {
                "selected": "---",
                "options": [],
            },
        }

        for n, i in enumerate(place['breadcrumbs'], start=1):
            lists[n]['selected'] = i['slug']
        
        # at this point, at least a country will be selected, get its pk
        top_pk = Place.objects.get(slug=lists[1]["selected"]).pk

        # always give all of the country options
        all_lvl1 = list(Place.objects.filter(direct_parents=None).values("pk", "slug", "name", "volume_count_inclusive"))
        lists[1]["options"] = all_lvl1

        all_lvl2 = list(Place.objects.filter(direct_parents=top_pk).values("pk", "slug", "name", "volume_count_inclusive"))
        lists[2]["options"] = all_lvl2

        # if a state is selected, set options to all other states in the same country
        # also, set county and city options
        if lists[2]['selected'] != "---":
            state_pk = Place.objects.get(slug=lists[2]["selected"]).pk
            all_lvl3 = list(Place.objects.filter(direct_parents=state_pk).values("pk", "slug", "name", "volume_count_inclusive"))
            lists[3]["options"] = all_lvl3
            lvl3_pks = [i['pk'] for i in all_lvl3]
            all_lvl4 = list(Place.objects.filter(direct_parents__in=lvl3_pks).values("pk", "slug", "name", "volume_count_inclusive"))
            lists[4]["options"] = all_lvl4

        # if a county/parish is selected, narrow cities to only those in the county
        if lists[3]['selected'] != "---":
            ce_pk = Place.objects.get(slug=lists[3]["selected"]).pk
            all_lvl4 = list(Place.objects.filter(direct_parents=ce_pk).values("pk", "slug", "name", "volume_count_inclusive"))
            lists[4]["options"] = all_lvl4

        for k, v in lists.items():
            v['options'].sort(key=lambda k : k['name'])

        if f == "json":
            return JsonResponse({
                "PLACE": place,
                "LISTS": lists,
            })

        else:
            context_dict = {
                "params": {
                    "PAGE_NAME": 'place',
                    "PARAMS": {
                        "PLACE": place,
                        "LISTS": lists,
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
