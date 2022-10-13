import os
import json
import logging
from datetime import datetime

from django.contrib.gis.geos import GEOSGeometry
from django.shortcuts import render, get_object_or_404
from django.views import View
from django.urls import reverse
from django.http import JsonResponse, Http404, HttpResponse
from django.middleware import csrf
from django.conf import settings
from django.views.decorators.clickjacking import xframe_options_exempt

from georeference.utils import full_reverse
from georeference.models.resources import Layer

from loc_insurancemaps.models import Volume, Place
from loc_insurancemaps.utils import unsanitize_name, filter_volumes_for_use
from loc_insurancemaps.api import CollectionConnection
from loc_insurancemaps.tasks import load_docs_as_task

logger = logging.getLogger(__name__)

def get_user_type(user):
    if user.is_superuser:
        user_type = "superuser"
    elif user.is_authenticated:
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
            "index.html",
            context=context_dict
        )

class Browse(View):

    def get(self, request):

        started_volumes = Volume.objects.filter(status="started").order_by("city", "year")
        lc = CollectionConnection(delay=0)
        city_list = lc.get_city_list_by_state("louisiana")

        loaded_summary = []
        places_dict = {}
        for vol in started_volumes:
            loaded_by_name, loaded_by_profile = "", ""
            if vol.loaded_by is not None:
                loaded_by_name = vol.loaded_by.username,
                loaded_by_profile = reverse("profile_detail", args=(vol.loaded_by.username, )),

            items = vol.sort_lookups()
            year_vol = vol.year
            if vol.volume_no is not None:
                year_vol = f"{vol.year} vol. {vol.volume_no}"

            unprep_ct = len(items['unprepared'])
            prep_ct = len(items['prepared'])
            georef_ct = len(items['georeferenced'])
            percent = 0
            if georef_ct > 0:
                percent = int((georef_ct / (unprep_ct + prep_ct + georef_ct)) * 100)

            main_lyrs_ct = 0
            if vol.sorted_layers:
                main_lyrs_ct = len(vol.sorted_layers['main'])
            mm_ct, mm_todo = 0, 0
            mm_display = f"0/{main_lyrs_ct}"
            if vol.multimask is not None:
                mm_ct = len(vol.multimask)
                mm_todo = main_lyrs_ct - mm_ct
                if mm_ct > 0:
                    mm_display = f"{mm_ct}/{main_lyrs_ct}"

            viewer_url = ""
            if vol.locale:
                full_reverse("viewer", args=(vol.locale.slug,)) + f"?year={vol.year}",
                place_name = vol.locale.name
                if len(vol.locale.direct_parents.all()) > 0:
                    place_name = f"{place_name}, {vol.locale.direct_parents.all()[0].__str__()}"
            else:
                place_name = f"{vol.city}, {vol.county_equivalent}, {vol.state}"

            vol_content = {
                "identifier": vol.identifier,
                "city": vol.city,
                "county_equivalent": vol.county_equivalent,
                "state": vol.state,
                "place_name": place_name,
                "year_vol": year_vol,
                "sheet_ct": vol.sheet_ct,
                "unprepared_ct": unprep_ct,
                "prepared_ct": prep_ct,
                "georeferenced_ct": georef_ct,
                "percent": percent,
                "volume_no": vol.volume_no,
                "loaded_by_name": loaded_by_name,
                "loaded_by_profile": loaded_by_profile,
                "title": vol.__str__(),
                "mm_ct": mm_todo,
                "mm_display": mm_display,
                "urls": {
                    "summary": full_reverse("volume_summary", args=(vol.identifier,)),
                    "viewer": viewer_url,
                }
            }
            loaded_summary.append(vol_content)
            if vol.locale:
                places_dict[vol.locale] = places_dict.get(vol.locale, []) + [vol_content]

        places = []
        for place, volumes in places_dict.items():
            name = place.name
            if len(place.direct_parents.all()) > 0:
                name = f"{name}, {place.direct_parents.all()[0].__str__()}"
            p_content = {
                "name": name,
                "url": full_reverse("viewer", args=(place.slug,)),
                "volumes": volumes,
                "sort_years": ", ".join(sorted([str(i['year_vol']) for i in volumes])),
            }
            places.append(p_content)

        context_dict = {
            "browse_params": {
                "STARTED_VOLUMES": loaded_summary,
                "PLACES": places,
            },
        }
        return render(
            request,
            "browse.html",
            context=context_dict
        )

class VolumeTrim(View):

    def get(self, request, volumeid):

        volume = get_object_or_404(Volume, pk=volumeid)
        volume_json = volume.serialize()

        volume_json['sorted_layers']['main'].sort(key=lambda item: item.get("name"))

        gs = os.getenv("GEOSERVER_LOCATION", "http://localhost:8080/geoserver/")
        gs = gs.rstrip("/") + "/"
        geoserver_ows = f"{gs}ows/"

        context_dict = {
            "svelte_params": {
                "USE_TITILER": settings.USE_TITILER,
                "TITILER_HOST": settings.TITILER_HOST,
                "SESSION_LENGTH": settings.GEOREFERENCE_SESSION_LENGTH,
                "VOLUME": volume_json,
                "CSRFTOKEN": csrf.get_token(request),
                'USER_TYPE': get_user_type(request.user),
                'GEOSERVER_WMS': geoserver_ows,
                "MAPBOX_API_KEY": settings.MAPBOX_API_TOKEN,
            }
        }
        return render(
            request,
            "lc/volume_trim.html",
            context=context_dict
        )

    def post(self, request, volumeid):

        volume = get_object_or_404(Volume, pk=volumeid)

        body = json.loads(request.body)
        multimask = body.get('multiMask')

        # data validation
        if multimask is not None and isinstance(multimask, dict):
            for k, v in multimask.items():
                try:
                    geom_str = json.dumps(v['geometry'])
                    GEOSGeometry(geom_str)
                except Exception as e:
                    logger.error(f"{volumeid} | improper GeoJSON in multimask: {k}")
                    return JsonResponse({"status": "error"})

            volume.multimask = multimask
            volume.save()
        
        volume_json = volume.serialize()
        response = {
            "status": "ok",
            "volume_json": volume_json
        }

        return JsonResponse(response)


class VolumeDetail(View):

    def get(self, request, volumeid):

        volume = get_object_or_404(Volume, pk=volumeid)
        volume_json = volume.serialize()

        other_vols = []
        for v in Volume.objects.filter(city=volume.city):
            url = reverse("volume_summary", args=(v.pk, ))
            if v.pk == volume.pk:
                url = None
            item = {
                "name": v.__str__(),
                "year": str(v.year),
                "url": url,
            }
            if v.volume_no is not None:
                item['year'] += f" vol. {v.volume_no}"
            other_vols.append(item)
        other_vols.sort(key=lambda i: i['year'])

        gs = os.getenv("GEOSERVER_LOCATION", "http://localhost:8080/geoserver/")
        gs = gs.rstrip("/") + "/"
        geoserver_ows = f"{gs}ows/"

        context_dict = {
            "svelte_params": {
                "USE_TITILER": settings.USE_TITILER,
                "TITILER_HOST": settings.TITILER_HOST,
                "VOLUME": volume_json,
                "OTHER_VOLUMES": other_vols,
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
            volume = Volume.objects.get(pk=volumeid)
            if volume.loaded_by is None:
                volume.loaded_by = request.user
                volume.load_date = datetime.now()
                volume.save(update_fields=["loaded_by", "load_date"])
            load_docs_as_task.apply_async(
                (volumeid, ),
                queue="update"
            )
            volume_json = volume.serialize()
            volume_json["status"] = "initializing..."

            return JsonResponse(volume_json)

        elif operation == "set-index-layers":

            volume = Volume.objects.get(pk=volumeid)

            index_layers = body.get("indexLayerIds", [])

            volume.sorted_layers["key_map"] = index_layers
            # remove key map layers from main layer list
            volume.sorted_layers["main"] = [i for i in volume.sorted_layers['main'] if not i in index_layers]
            # move old key map layers back into the main layer list
            for l in volume.layer_lookup.keys():
                if not l in volume.sorted_layers["main"] and not l in index_layers:
                    volume.sorted_layers["main"].append(l)

            volume.save(update_fields=["sorted_layers"])
            volume_json = volume.serialize()
            return JsonResponse(volume_json)

        elif operation == "refresh":
            volume = Volume.objects.get(pk=volumeid)
            volume_json = volume.serialize()
            return JsonResponse(volume_json)

        elif operation == "refresh-lookups":
            volume = Volume.objects.get(pk=volumeid)
            volume.refresh_lookups()
            volume_json = volume.serialize()
            return JsonResponse(volume_json)


class PlaceView(View):

    def get(self, request, place_slug):

        p = Place.objects.filter(slug=place_slug)

        if p.count() == 1:
            data = p[0].serialize()
        else:
            data = {"place count": p.count()}

        context_dict = {
            "svelte_params": {
                "PLACE": data,
                "MAPBOX_API_KEY": settings.MAPBOX_API_TOKEN,
            }
        }
        return render(
            request,
            "loc/city_summary.html",
            context=context_dict
        )


class Viewer(View):

    @xframe_options_exempt
    def get(self, request, place_slug):

        year_to_show = request.GET.get("year")
        year_found = False

        place_data = {}
        volumes = []

        p = Place.objects.filter(slug=place_slug)
        if p.count() == 1:
            place = p[0]
        else:
            place = Place.objects.get(slug="louisiana")

        place_data = place.serialize()
        for v in Volume.objects.filter(locale=place).order_by("year","volume_no"):
            volumes.append(v.serialize())

            if not year_found:
                if year_to_show is not None:
                    if str(v.year) == str(year_to_show):
                        year_to_show = v.year
                        year_found = True
                else:
                    if len(v.sorted_layers['main']) > 0:
                        year_to_show = v.year
                        year_found = True

        gs = os.getenv("GEOSERVER_LOCATION", "http://localhost:8080/geoserver/")
        gs = gs.rstrip("/") + "/"
        geoserver_ows = f"{gs}ows/"

        context_dict = {
            "svelte_params": {
                "PLACE": place_data,
                "VOLUMES": volumes,
                "SHOW_YEAR": year_to_show,
                "USE_TITILER": settings.USE_TITILER,
                "TITILER_HOST": settings.TITILER_HOST,
                "GEOSERVER_WMS": geoserver_ows,
                "MAPBOX_API_KEY": settings.MAPBOX_API_TOKEN,
            }
        }
        return render(
            request,
            "viewer.html",
            context=context_dict
        )


class SimpleAPI(View):

    def get(self, request):
        qtype = request.GET.get("t", None)
        state = request.GET.get("s", None)
        city = request.GET.get("c", None)

        lc = CollectionConnection(delay=0, verbose=True)

        ## returns a list of all cities with volumes in this state
        if qtype == "cities":
            city_list = lc.get_city_list_by_state(state)
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

def get_layer_mrm_urls(layerid):

    return {
        "geotiff": full_reverse("mrm_get_resource", args=(layerid,)).rstrip("/") + "?resource=geotiff",
        "jpg": full_reverse("mrm_get_resource", args=(layerid,)).rstrip("/") + "?resource=jpg",
        "points": full_reverse("mrm_get_resource", args=(layerid,)).rstrip("/") + "?resource=points",
    }

class MRMEndpointList(View):

    def get(self, request):

        output = {}
        for l in Layer.objects.all().order_by("slug"):
            output[l.slug] = get_layer_mrm_urls(l.slug)

        return JsonResponse(output)

class MRMEndpointLayer(View):

    def get(self, request, layerid):

        if layerid.startswith("geonode:"):
            layerid = layerid.replace("geonode:", "")

        layer = get_object_or_404(Layer, slug=layerid)
        item = request.GET.get("resource", None)

        if item is None:
            return JsonResponse(get_layer_mrm_urls(layerid))

        elif item == "geotiff":
            if layer.file:
                with open(layer.file.path, 'rb') as fh:
                    response = HttpResponse(fh.read(), content_type="image/tiff")
                    response['Content-Disposition'] = f'inline; filename={layerid}.tiff'
                    return response
            raise Http404

        elif item == "points":
            content = layer.get_document().gcp_group.as_points_file()
            response = HttpResponse(content, content_type='text/plain')
            response['Content-Disposition'] = f'attachment; filename={layerid}.points'
            return response

        elif item == "jpg":
            doc_path = layer.get_document().file.path
            if os.path.exists(doc_path):
                with open(doc_path, 'rb') as fh:
                    response = HttpResponse(fh.read(), content_type="image/jpg")
                    response['Content-Disposition'] = f'inline; filename={layerid}.jpg'
                    return response
            raise Http404

        else:
            raise Http404
