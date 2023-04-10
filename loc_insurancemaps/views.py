import os
import re
import json
import logging
from datetime import datetime

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.gis.geos import GEOSGeometry, Polygon
from django.http import JsonResponse, Http404, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.views import View
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.middleware import csrf

# from geonode.base.api.serializers import UserSerializer

from georeference.utils import full_reverse
from georeference.models.sessions import SessionBase
from georeference.models.resources import GCP, Layer

from loc_insurancemaps.models import Volume
from loc_insurancemaps.utils import LOCConnection, unsanitize_name, filter_volumes_for_use
from loc_insurancemaps.tasks import load_docs_as_task

from places.models import Place

if settings.ENABLE_NEWSLETTER:
    from newsletter.models import Newsletter, Subscription

logger = logging.getLogger(__name__)

def get_user_type(user):
    if user.is_superuser:
        user_type = "superuser"
    elif user.is_authenticated:
        user_type = "participant"
    else:
        user_type = "anonymous"
    return user_type

def mobile(request):
    """Return True if the request comes from a mobile device."""

    MOBILE_AGENT_RE=re.compile(r".*(iphone|mobile|androidtouch)",re.IGNORECASE)

    if MOBILE_AGENT_RE.match(request.META['HTTP_USER_AGENT']):
        return True
    else:
        return False

class HomePage(View):

    def get(self, request):

        newsletter_slug = None
        user_subscribed = None
        if settings.ENABLE_NEWSLETTER:
            newsletter = None
            if Newsletter.objects.all().exists():
                newsletter = Newsletter.objects.all()[0]
                newsletter_slug = newsletter.slug
            if newsletter is not None and request.user.is_authenticated:
                user_subscription = Subscription.objects.filter(newsletter=newsletter, user=request.user)
                if user_subscription.exists() and user_subscription[0].subscribed is True:
                    user_subscribed = True
        user_email = ""
        if request.user.is_authenticated and request.user.email is not None:
            user_email = request.user.email

        viewer_showcase = None
        if settings.VIEWER_SHOWCASE_SLUG:
            try:
                p = Place.objects.get(slug=settings.VIEWER_SHOWCASE_SLUG)
                viewer_showcase = {
                    'name': p.name,
                    'url': reverse('viewer', args=(settings.VIEWER_SHOWCASE_SLUG,))
                }
            except Place.DoesNotExist:
                pass

        context_dict = {
            "search_params": {
                "CITY_QUERY_URL": reverse('lc_api'),
                'USER_TYPE': get_user_type(request.user),
                # 'CITY_LIST': city_list,
            },
            "svelte_params": {
                "PLACES_GEOJSON_URL": reverse("api-beta:places_geojson"),
                "IS_MOBILE": mobile(request),
                "CSRFTOKEN": csrf.get_token(request),
                "OHMG_API_KEY": settings.OHMG_API_KEY,
                "NEWSLETTER_SLUG": newsletter_slug,
                "USER_SUBSCRIBED": user_subscribed,
                "USER_EMAIL": user_email,
                "VIEWER_SHOWCASE": viewer_showcase,
            },
        }

        return render(
            request,
            "index.html",
            context=context_dict
        )

class Browse(View):

    def get(self, request):

        context_dict = {
            "browse_params": {
                "PLACES_GEOJSON_URL": reverse("api-beta:places_geojson"),
                "PLACES_CT": Place.objects.all().exclude(volume_count=0).count(),
                "PLACES_API_URL": reverse("api-beta:place_list"),
                "ITEM_CT": Volume.objects.all().exclude(loaded_by=None).count(),
                "ITEM_API_URL": reverse("api-beta:item_list"),
                "OHMG_API_KEY": settings.OHMG_API_KEY,
            },
        }
        return render(
            request,
            "browse.html",
            context=context_dict
        )

class VolumeTrim(View):

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
        volume_json = volume.serialize(include_session_info=True)

        other_vols = []
        for v in Volume.objects.filter(city=volume.city):
            url = reverse("volume_summary", args=(v.pk, ))
            if v.pk == volume.pk:
                url = None
            item = {
                "alt": v.__str__(),
                "display": str(v.year),
                "url": url,
            }
            if v.volume_no is not None:
                item['display'] += f" vol. {v.volume_no}"
            other_vols.append(item)
        other_vols.sort(key=lambda i: i['display'])

        gs = os.getenv("GEOSERVER_LOCATION", "http://localhost:8080/geoserver/")
        gs = gs.rstrip("/") + "/"
        geoserver_ows = f"{gs}ows/"

        context_dict = {
            "svelte_params": {
                "TITILER_HOST": settings.TITILER_HOST,
                "VOLUME": volume_json,
                "OTHER_VOLUMES": other_vols,
                "CSRFTOKEN": csrf.get_token(request),
                'USER_TYPE': get_user_type(request.user),
                "MAPBOX_API_KEY": settings.MAPBOX_API_TOKEN,
            }
        }
        return render(
            request,
            "loc_insurancemaps/volume_summary.html",
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
            load_docs_as_task.delay(volumeid)
            volume_json = volume.serialize(include_session_info=True)
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
            volume_json = volume.serialize(include_session_info=True)
            return JsonResponse(volume_json)

        elif operation == "refresh":
            volume = Volume.objects.get(pk=volumeid)
            volume_json = volume.serialize(include_session_info=True)
            return JsonResponse(volume_json)

        elif operation == "refresh-lookups":
            volume = Volume.objects.get(pk=volumeid)
            volume.refresh_lookups()
            volume_json = volume.serialize(include_session_info=True)
            return JsonResponse(volume_json)


class SimpleAPI(View):

    def get(self, request):
        qtype = request.GET.get("t", None)
        state = request.GET.get("s", None)
        city = request.GET.get("c", None)

        lc = LOCConnection(delay=0, verbose=True)

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
        "gcps-geojson": full_reverse("mrm_get_resource", args=(layerid,)).rstrip("/") + "?resource=gcps-geojson",
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

        elif item == "gcps-geojson":
            return JsonResponse(layer.get_document().gcp_group.as_geojson)

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
