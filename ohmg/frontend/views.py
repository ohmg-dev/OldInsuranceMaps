import os
import logging
from pathlib import Path

import frontmatter

from django.conf import settings
from django.http import JsonResponse, Http404, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.views import View
from django.views.decorators.clickjacking import xframe_options_sameorigin

from newsletter.models import Submission, Message

from ohmg.context_processors import generate_ohmg_context
from ohmg.utils import full_reverse
from ohmg.georeference.models import Layer
from ohmg.georeference.schemas import AnnotationSetSchema

from ohmg.loc_insurancemaps.models import Volume

from ohmg.places.models import Place


if settings.ENABLE_NEWSLETTER:
    from newsletter.models import Newsletter, Subscription

logger = logging.getLogger(__name__)


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

        context_dict = {
            "params": {
                "CONTEXT": generate_ohmg_context(request),
                "PAGE_NAME": 'home',
                'PARAMS': {
                    "NEWSLETTER_SLUG": newsletter_slug,
                    "USER_SUBSCRIBED": user_subscribed,
                    "PLACES_CT": Place.objects.all().exclude(volume_count=0).count(),
                    "MAP_CT": Volume.objects.all().exclude(loaded_by=None).count(),
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
                "CONTEXT": generate_ohmg_context(request),
                "PAGE_NAME": 'browse',
                "PARAMS": {
                    "PLACES_CT": Place.objects.all().exclude(volume_count=0).count(),
                    "MAP_CT": Volume.objects.all().exclude(loaded_by=None).count(),
                }
            }
        }
        return render(
            request,
            "index.html",
            context=context_dict
        )

class ActivityView(View):

    def get(self, request):

        context_dict = {
            "params": {
                "CONTEXT": generate_ohmg_context(request),
                "PAGE_NAME": 'activity',
            }
        }

        return render(
            request,
            "index.html",
            context=context_dict
        )
    
class MarkdownPage(View):

    def get(self, request, slug):

        md_path = Path(settings.PROJECT_DIR, 'frontend', 'pages', f"{slug}.md")
        if not os.path.isfile(md_path):
            raise Http404

        post = frontmatter.load(md_path)

        context_dict = {
            "params": {
                "PAGE_TITLE": post['page_title'],
                "PAGE_NAME": 'markdown-page',
                "PARAMS": {
                    "HEADER": post['header'],
                    # downstream SvelteMarkdown requires this variable to be `source`
                    "source": post.content,
                }
            }
        }

        return render(
            request,
            "index.html",
            context=context_dict
        )

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
        for lyr in Layer.objects.all().order_by("slug"):
            output[lyr.slug] = get_layer_mrm_urls(lyr.slug)

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
            v_serialized = v.serialize()
            v_serialized['main_annotation_set'] = AnnotationSetSchema.from_orm(v.get_annotation_set('main-content')).dict()
            volumes.append(v_serialized)

        context_dict = {
            "svelte_params": {
                "CONTEXT": generate_ohmg_context(request),
                "PLACE": place_data,
                "VOLUMES": volumes,
            }
        }
        return render(
            request,
            "viewer.html",
            context=context_dict
        )
