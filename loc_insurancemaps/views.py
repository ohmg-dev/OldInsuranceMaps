import os
import json
import logging
from datetime import datetime

from django.contrib.gis.geos import GEOSGeometry
from django.shortcuts import render, get_object_or_404
from django.views import View
from django.urls import reverse
from django.http import JsonResponse, Http404, HttpResponse, HttpResponseRedirect
from django.middleware import csrf
from django.conf import settings

from geonode.base.models import Region
from geonode.layers.models import Layer, LayerFile
from geonode.groups.conf import settings as groups_settings

from georeference.proxy_models import LayerProxy
from georeference.utils import full_reverse

from loc_insurancemaps.models import Volume, Place
from .utils import unsanitize_name, filter_volumes_for_use
from .api import CollectionConnection
from .tasks import load_documents_as_task

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
            "index.html",
            context=context_dict
        )

class Browse(View):

    def get(self, request):

        started_volumes = Volume.objects.filter(status="started").order_by("city", "year")
        lc = CollectionConnection(delay=0)
        city_list = lc.get_city_list_by_state("louisiana")

        loaded_summary = []
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
            if vol.ordered_layers:
                main_lyrs_ct = len(vol.ordered_layers['layers'])
            mm_ct = 0
            mm_display = f"0/{main_lyrs_ct}"
            if vol.multimask is not None:
                mm_ct = len(vol.multimask)
                if mm_ct > 0:
                    mm_display = f"{mm_ct}/{main_lyrs_ct}"

            if vol.locale:
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
                "mm_ct": mm_ct,
                "mm_display": mm_display,
                "urls": {
                    "summary": reverse("volume_summary", args=(vol.identifier,))
                }
            }
            loaded_summary.append(vol_content)

        place_pks = Volume.objects.all().filter(status="started").values_list("locale", flat=True)
        place_objects = Place.objects.filter(pk__in=place_pks).order_by("name")

        places = []
        for p in place_objects:
            volume_links = []
            vols = Volume.objects.filter(locale=p).order_by("year", "volume_no")
            first_year = None
            for v in vols:
                if len(v.ordered_layers['layers']) > 0:
                    if first_year is None:
                        first_year = str(v.year)
                    display_val = str(v.year)
                    if v.volume_no is not None:
                        display_val += f" vol. {v.volume_no}"
                    volume_links.append({
                        "display_val": display_val,
                        "viewer_url": full_reverse("viewer") + f"?place={p.slug}&year={v.year}",
                    })
            if len(volume_links) > 0:
                name = p.name
                if len(p.direct_parents.all()) > 0:
                    name = f"{name}, {p.direct_parents.all()[0].__str__()}"
                places.append({
                    "name": name,
                    "url": full_reverse("viewer") + f"?place={p.slug}",
                    "volumes": volume_links,
                    "sort_years": ", ".join(sorted([i['display_val'] for i in volume_links])),
                })

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

        volume_json['ordered_layers']['layers'].sort(key=lambda item: item.get("name"))

        gs = os.getenv("GEOSERVER_LOCATION", "http://localhost:8080/geoserver/")
        gs = gs.rstrip("/") + "/"
        geoserver_ows = f"{gs}ows/"

        context_dict = {
            "svelte_params": {
                "USE_TITILER": settings.USE_TITILER,
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
            load_documents_as_task.apply_async(
                (volumeid, ),
                queue="update"
            )
            volume_json = volume.serialize()
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

        elif operation == "refresh-lookups":
            volume = Volume.objects.get(pk=volumeid)
            volume.populate_lookups()
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

    def get(self, request):

        place_slug = request.GET.get("place", "louisiana")
        year_to_show = request.GET.get("year")
        year_found = False

        place_data = {}
        volumes = []
        if place_slug is not None:
            p = Place.objects.filter(slug=place_slug)
            if p.count() == 1:
                place = p[0]
                place_data = place.serialize()
                for v in Volume.objects.filter(locale=place).order_by("year","volume_no"):
                    volumes.append(v.serialize())

                    if not year_found:
                        if year_to_show is not None:
                            if str(v.year) == str(year_to_show):
                                year_to_show = v.year
                                year_found = True
                        else:
                            if len(v.ordered_layers['layers']) > 0:
                                year_to_show = v.year
                                year_found = True

            else:
                place_data = {"place count": p.count()}

        gs = os.getenv("GEOSERVER_LOCATION", "http://localhost:8080/geoserver/")
        gs = gs.rstrip("/") + "/"
        geoserver_ows = f"{gs}ows/"

        context_dict = {
            "svelte_params": {
                "PLACE": place_data,
                "VOLUMES": volumes,
                "SHOW_YEAR": year_to_show,
                "USE_TITILER": settings.USE_TITILER,
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

def get_layer_mrm_urls(layerid):

    return {
        "geotiff": full_reverse("mrm_get_resource", args=(layerid,)).rstrip("/") + "?resource=geotiff",
        "jpg": full_reverse("mrm_get_resource", args=(layerid,)).rstrip("/") + "?resource=jpg",
        "points": full_reverse("mrm_get_resource", args=(layerid,)).rstrip("/") + "?resource=points",
    }

class MRMEndpointList(View):

    def get(self, request):

        output = {}
        for l in Layer.objects.all().order_by("alternate"):
            layerid = l.alternate.replace("geonode:", "")
            output[layerid] = get_layer_mrm_urls(layerid)

        return JsonResponse(output)

class MRMEndpointLayer(View):

    def get(self, request, layerid):

        if not layerid.startswith("geonode:"):
            layeralt = "geonode:" + layerid
        else:
            layeralt = layerid
        lp = LayerProxy(layeralt, raise_404_on_error=True)
        item = request.GET.get("resource", None)

        if item is None:
            return JsonResponse(get_layer_mrm_urls(layerid))

        elif item == "geotiff":
            lf = LayerFile.objects.filter(upload_session=lp.get_layer().upload_session)
            if len(lf) == 1:
                file_path = lf[0].file.path
                if os.path.exists(file_path):
                    with open(file_path, 'rb') as fh:
                        response = HttpResponse(fh.read(), content_type="image/tiff")
                        response['Content-Disposition'] = f'inline; filename={layerid}.tiff'
                        return response
            raise Http404

        elif item == "points":
            content = lp.get_document_proxy().gcp_group.as_points_file()
            response = HttpResponse(content, content_type='text/plain')
            response['Content-Disposition'] = f'attachment; filename={layerid}.points'
            return response

        elif item == "jpg":
            file_path = lp.get_document().doc_file.path
            if os.path.exists(file_path):
                with open(file_path, 'rb') as fh:
                    response = HttpResponse(fh.read(), content_type="image/jpg")
                    response['Content-Disposition'] = f'inline; filename={layerid}.jpg'
                    return response
            raise Http404

        else:
            raise Http404
