import os
import json
import logging

from django.shortcuts import render, get_object_or_404
from django.views import View
from django.urls import reverse
from django.http import JsonResponse
from django.middleware import csrf
from django.conf import settings

from geonode.base.models import Region
from geonode.layers.models import Layer
from geonode.groups.conf import settings as groups_settings

from .models import Volume
from .utils import unsanitize_name, filter_volumes_for_use
from .enumerations import STATE_CHOICES
from .api import CollectionConnection
from .tasks import import_sheets_as_task

logger = logging.getLogger(__name__)


def get_user_type(user):
    if user.is_superuser:
        user_type = "superuser"
    elif user.groups.filter(name=groups_settings.REGISTERED_MEMBERS_GROUP_NAME).exists():
        user_type = "participant"
    else:
        user_type = "anonymous"
    return user_type


class HomePage(View):

    def get(self, request):

        lc = CollectionConnection(delay=0)
        city_list = lc.get_city_list_by_state("louisiana")
        context_dict = {
            "search_params": {
                "CITY_QUERY_URL": reverse('lc_api'),
                'USER_TYPE': get_user_type(request.user),
                'CITY_LIST': city_list,
            }
        }

        return render(
            request,
            "site_index.html",
            context=context_dict
        )

class Volumes(View):

    def get(self, request):

        started_volumes = Volume.objects.filter(status="started").order_by("city", "year")
        lc = CollectionConnection(delay=0)
        city_list = lc.get_city_list_by_state("louisiana")

        loaded_summary = []
        for vol in started_volumes:
            items = vol.sort_lookups()
            year_vol = vol.year
            if vol.volume_no is not None:
                year_vol = f"{vol.year} vol. {vol.volume_no}"
            vol_content = {
                "identifier": vol.identifier,
                "city": vol.city,
                "county_equivalent": vol.county_equivalent,
                "state": vol.state,
                "year_vol": year_vol,
                "sheet_ct": vol.sheet_ct,
                "unprepared_ct": len(items['unprepared']),
                "prepared_ct": len(items['prepared']),
                "georeferenced_ct": len(items['georeferenced']),
                "volume_no": vol.volume_no,
                "loaded_by": {
                    "name": vol.loaded_by.username,
                    "profile": reverse("profile_detail", args=(vol.loaded_by.username, )),
                },
                "title": vol.__str__(),
                "urls": {
                    "summary": reverse("volume_summary", args=(vol.identifier,))
                }
            }
            loaded_summary.append(vol_content)

        context_dict = {
            "list_params": {
                "STARTED_VOLUMES": loaded_summary,
            },
            "search_params": {
                "CITY_QUERY_URL": reverse('lc_api'),
                'USER_TYPE': get_user_type(request.user),
                'CITY_LIST': city_list,
            }
        }
        return render(
            request,
            "lc/volumes.html",
            context=context_dict
        )

class VolumeDetail(View):

    def get(self, request, volumeid):

        volume = get_object_or_404(Volume, pk=volumeid)
        volume_json = volume.serialize()

        gs = os.getenv("GEOSERVER_LOCATION", "http://localhost:8080/geoserver/")
        gs = gs.rstrip("/") + "/"
        geoserver_ows = f"{gs}ows/"

        context_dict = {
            "svelte_params": {
                "VOLUME": volume_json,
                "CSRFTOKEN": csrf.get_token(request),
                'USER_TYPE': get_user_type(request.user),
                'GEOSERVER_WMS': geoserver_ows,
                "MAPBOX_API_KEY": settings.MAPBOX_API_TOKEN,
            }
        }
        return render(
            request,
            "lc/volume_summary.html",
            context=context_dict
        )

    def post(self, request, volumeid):

        body = json.loads(request.body)
        operation = body.get("operation", None)

        if operation == "initialize":
            import_sheets_as_task.apply_async(
                (volumeid, request.user.pk),
                queue="update"
            )
            volume = Volume.objects.get(pk=volumeid)
            volume_json = volume.serialize()

            # set a few things manually here that may not be set on the Volume
            # yet due to async operations
            volume_json["loaded_by"] = {
                "name": request.user.username,
                "profile": reverse("profile_detail", args=(request.user.username, )),
            }
            volume_json["status"] = "initializing..."

            return JsonResponse(volume_json)

        elif operation == "set-index-layers":

            volume = Volume.objects.get(pk=volumeid)

            index_layers = body.get("indexLayerIds", [])

            volume.ordered_layers["index_layers"] = index_layers
            # remove key map layers from main layer list
            volume.ordered_layers["layers"] = [i for i in volume.ordered_layers['layers'] if not i in index_layers]
            # move old key map layers back into the main layer list
            for l in volume.layer_lookup.keys():
                if not l in volume.ordered_layers["layers"] and not l in index_layers:
                    volume.ordered_layers["layers"].append(l)

            volume.save(update_fields=["ordered_layers"])
            volume_json = volume.serialize()
            return JsonResponse(volume_json)

        elif operation == "set-layer-order":

            volume = Volume.objects.get(pk=volumeid)
            volume.ordered_layers["layers"] = body.get("layerIds", [])
            volume.ordered_layers["index_layers"] = body.get("indexLayerIds", [])
            volume.save(update_fields=["ordered_layers"])

            volume_json = volume.serialize()
            return JsonResponse(volume_json)

        elif operation == "refresh":
            volume = Volume.objects.get(pk=volumeid)
            volume_json = volume.serialize()
            return JsonResponse(volume_json)

class SimpleAPI(View):

    def get(self, request):
        qtype = request.GET.get("t", None)
        state = request.GET.get("s", None)
        city = request.GET.get("c", None)

        lc = CollectionConnection(delay=0, verbose=True)

        ## returns a list of all cities with volumes in this state
        if qtype == "cities":
            city_list = lc.get_city_list_by_state(state)
            missing = []
            for i in city_list:
                try:
                    reg = Region.objects.get(name__iexact=i[0])
                except Region.DoesNotExist:
                    missing.append(i)

            return JsonResponse(city_list, safe=False)

        ## return a list of all volumes in a city
        elif qtype == "volumes":

            city = unsanitize_name(state, city)
            volumes = lc.get_volume_list_by_city(city, state)

            ## a little bit of post-processing on the volume list
            volumes = filter_volumes_for_use(volumes)

            return JsonResponse(volumes, safe=False)
        
        else:
            return JsonResponse({})