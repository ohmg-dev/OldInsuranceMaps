import logging

from natsort import natsorted

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import Http404
from django.shortcuts import render, get_object_or_404
from django.views import View
from django.views.decorators.clickjacking import xframe_options_sameorigin

from ohmg.core.context_processors import generate_ohmg_context
from ohmg.core.models import Map
from ohmg.core.api.schemas import (
    LayerSetSchema,
    MapFullSchema,
)

from ohmg.places.models import Place


if settings.ENABLE_NEWSLETTER:
    from newsletter.models import (
        Newsletter,
        Subscription,
        Submission,
        Message,
    )

logger = logging.getLogger(__name__)


def newsletter_context(request):
    newsletter_slug = None
    user_subscribed = False
    newsletter = None
    if Newsletter.objects.all().exists():
        newsletter = Newsletter.objects.all()[0]
        newsletter_slug = newsletter.slug
    if newsletter is not None and request.user.is_authenticated:
        user_subscription = Subscription.objects.filter(newsletter=newsletter, user=request.user)
        if user_subscription.exists() and user_subscription[0].subscribed is True:
            user_subscribed = True

    return (newsletter_slug, user_subscribed)


class HomePage(View):
    def get(self, request):
        if settings.ENABLE_NEWSLETTER:
            newsletter_slug, user_subscribed = newsletter_context(request)
        else:
            newsletter_slug, user_subscribed = None, False

        all_maps = Map.objects.exclude(hidden=True).order_by("title")
        filter_list = [
            {"title": i[0], "id": i[1]} for i in all_maps.values_list("title", "identifier")
        ]
        featured_list = [
            {"title": i[0], "id": i[1]}
            for i in all_maps.filter(featured=True).values_list("title", "identifier")
        ]
        context_dict = {
            "params": {
                "CONTEXT": generate_ohmg_context(request),
                "PAGE_NAME": "home",
                "PARAMS": {
                    "NEWSLETTER_SLUG": newsletter_slug,
                    "USER_SUBSCRIBED": user_subscribed,
                    "PLACES_CT": Place.objects.all().exclude(volume_count=0).count(),
                    "MAP_CT": Map.objects.all().exclude(loaded_by=None).count(),
                    "FEATURED_MAPS": featured_list,
                    "MAP_FILTER_LIST": filter_list,
                },
            },
        }

        return render(request, "index.html", context=context_dict)


class Browse(View):
    def get(self, request):
        context_dict = {
            "params": {
                "CONTEXT": generate_ohmg_context(request),
                "PAGE_NAME": "browse",
                "PARAMS": {
                    "PLACES_CT": Place.objects.all().exclude(volume_count=0).count(),
                    "MAP_CT": Map.objects.all().exclude(loaded_by=None).count(),
                },
            }
        }
        return render(request, "index.html", context=context_dict)


class ActivityView(View):
    def get(self, request):
        all_maps = Map.objects.exclude(hidden=True).order_by("title")
        map_filter_list = [
            {"title": i[0], "id": i[1]} for i in all_maps.values_list("title", "identifier")
        ]
        users = get_user_model().objects.all()
        user_filter_list = natsorted(
            [{"title": i, "id": i} for i in users.values_list("username", flat=True)],
            key=lambda k: k["id"],
        )
        context_dict = {
            "params": {
                "CONTEXT": generate_ohmg_context(request),
                "PAGE_NAME": "activity",
                "PARAMS": {
                    "MAP_FILTER_LIST": map_filter_list,
                    "USER_FILTER_LIST": user_filter_list,
                },
            }
        }

        return render(request, "index.html", context=context_dict)


class NewsList(View):
    def get(self, request):
        newsletter_slug, user_subscribed = newsletter_context(request)

        submissions = Submission.objects.filter(publish=True).order_by("-publish_date")
        for s in submissions:
            ## consider it a "newsletter" post if it's been sent to more than one subscription
            ## the assumption being that a "blog" post will be sent to only the admin email address.
            if s.subscriptions.all().count() > 1:
                s.is_newsletter = True
            else:
                s.is_newsletter = False

        context_dict = {
            "submissions": submissions,
            "NEWSLETTER_SLUG": newsletter_slug,
            "USER_SUBSCRIBED": user_subscribed,
        }

        return render(request, "news/list.html", context=context_dict)


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

        return render(request, "news/article.html", context=context_dict)


class Viewer(View):
    @xframe_options_sameorigin
    def get(self, request, place_slug):
        place_data = {}
        maps = []

        p = Place.objects.filter(slug=place_slug)
        if p.count() == 1:
            place = p[0]
        else:
            place = Place.objects.get(slug="louisiana")

        place_data = place.serialize()
        for map in Map.objects.filter(locales__id__exact=place.id).prefetch_related():
            map_json = MapFullSchema.from_orm(map).dict()
            map_json["main_layerset"] = LayerSetSchema.from_orm(
                map.get_layerset("main-content")
            ).dict()
            maps.append(map_json)

        maps_sorted = natsorted(maps, key=lambda x: x["title"], reverse=True)

        context_dict = {
            "svelte_params": {
                "CONTEXT": generate_ohmg_context(request),
                "PLACE": place_data,
                "MAPS": maps_sorted,
            }
        }
        return render(request, "viewer.html", context=context_dict)
