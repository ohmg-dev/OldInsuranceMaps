import os
import re
import json
import logging
from datetime import datetime

from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry
from django.http import JsonResponse, Http404, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.views import View
from django.middleware import csrf

from newsletter.models import Submission, Message

from ohmg.utils import full_reverse
from ohmg.georeference.models import Layer

from ohmg.loc_insurancemaps.models import Volume
from ohmg.loc_insurancemaps.tasks import load_docs_as_task

from ohmg.places.models import Place

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
            "params": {
                "PAGE_NAME": 'home',
                'PARAMS': {
                    "ITEM_API_URL": reverse("api-beta:item_list"),
                    "SESSION_API_URL": reverse("api-beta:session_list"),
                    "PLACES_GEOJSON_URL": reverse("api-beta:places_geojson"),
                    "IS_MOBILE": mobile(request),
                    "CSRFTOKEN": csrf.get_token(request),
                    "OHMG_API_KEY": settings.OHMG_API_KEY,
                    "NEWSLETTER_SLUG": newsletter_slug,
                    "USER_SUBSCRIBED": user_subscribed,
                    "USER_EMAIL": user_email,
                    "VIEWER_SHOWCASE": viewer_showcase,
                    "PLACES_CT": Place.objects.all().exclude(volume_count=0).count(),
                    "ITEMS_CT": Volume.objects.all().exclude(loaded_by=None).count(),
                }
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
            "params": {
                "PAGE_NAME": 'browse',
                "PARAMS": {
                    "PLACES_GEOJSON_URL": reverse("api-beta:places_geojson"),
                    "PLACES_CT": Place.objects.all().exclude(volume_count=0).count(),
                    "PLACES_API_URL": reverse("api-beta:place_list"),
                    "ITEM_CT": Volume.objects.all().exclude(loaded_by=None).count(),
                    "ITEM_API_URL": reverse("api-beta:item_list"),
                    "OHMG_API_KEY": settings.OHMG_API_KEY,
                }
            }
        }
        return render(
            request,
            "index.html",
            context=context_dict
        )

class BasicPage(View):

    def get(self, request, slug, title):

        context_dict = {
            "params": {
                "PAGE_TITLE": title,
                "PAGE_NAME": slug,
                "PARAMS": {}
            }
        }

        if slug == "activity":
            context_dict['params']['PARAMS'].update({
                "SESSION_API_URL": reverse("api-beta:session_list"),
                "OHMG_API_KEY": settings.OHMG_API_KEY,
            })
        return render(
            request,
            "index.html",
            context=context_dict
        )

class VolumeTrim(View):

    def post(self, request, volumeid):

        volume = get_object_or_404(Volume, pk=volumeid)

        body = json.loads(request.body)
        multimask = body.get('multiMask')

        # data validation
        errors = []
        if multimask is not None and isinstance(multimask, dict):
            for k, v in multimask.items():
                try:
                    geom_str = json.dumps(v['geometry'])
                    g = GEOSGeometry(geom_str)
                    if not g.valid:
                        logger.error(f"{volumeid} | invalid mask: {k} - {g.valid_reason}")
                        errors.append((k, g.valid_reason))
                except Exception as e:
                    logger.error(f"{volumeid} | improper GeoJSON in multimask: {k}")
                    errors.append((k, e))
        if errors:
            response = {
                "status": "error",
                "errors": errors,
            }
        else:
            volume.multimask = multimask
            volume.save()
            response = {
                "status": "ok",
                "volume_json": volume.serialize()
            }

        return JsonResponse(response)


class VolumeDetail(View):

    def get(self, request, volumeid):

        volume = get_object_or_404(Volume, pk=volumeid)
        volume_json = volume.serialize(include_session_info=True)

        other_vols = []
        locale_slugs = [i.slug for i in volume.locales.all()]
        for v in Volume.objects.filter(city=volume.city, state=volume.state):
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
            "content/item.html",
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

            lcat_lookup = body.get("layerCategoryLookup", {})

            for cat in volume.sorted_layers:
                volume.sorted_layers[cat] = [k for k, v in lcat_lookup.items() if v == cat]

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
            response = layer.get_document().gcp_group.as_geojson
            response['warning'] = 'ATTENTION: this endpoint will be retired very soon. please get in touch with hello@oldinsurancemaps.net if you are interested in a replacement for it! Also just to say hi!'
            return JsonResponse(response)

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

class NewsList(View):

    def get(self, request):

        submissions = Submission.objects.filter(publish=True).order_by("-publish_date")
        for s in submissions:
            ## consider it a "newsletter" post if it's been sent to more than one subscription
            ## the assumption being that a "blog" post will be sent to only the admin email address.
            if s.subscriptions.all().count() > 1:
                s.is_newsletter = True
            else:
                s.is_newsletter = False

        context_dict = {
            "submissions": submissions
        }

        return render(
            request,
            "news/list.html",
            context=context_dict
        )

class NewsArticle(View):

    def get(self, request, slug):

        message = get_object_or_404(Message, slug=slug)
        submissions = Submission.objects.filter(message=message).order_by("-publish_date")
        if not submissions.exists():
            return Http404

        context_dict = {
            "message": message,
            "publish_date": submissions[0].publish_date,
        }

        return render(
            request,
            "news/article.html",
            context=context_dict
        )
