import logging

import humanize
from django.conf import settings
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.views import View

from ohmg.conf.http import generate_ohmg_context
from ohmg.core.models import Map
from ohmg.places.models import Place

from .models import Partner

if settings.ENABLE_NEWSLETTER:
    from newsletter.models import (
        Message,
        Newsletter,
        Submission,
        Subscription,
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
        featured_list = [
            {"title": i[0], "id": i[1]}
            for i in all_maps.filter(featured=True).values_list("title", "identifier")
        ]
        partners = [i.serialize() for i in Partner.objects.all()]
        partners.sort(key=lambda x: x["sortorder"])

        place_ct = humanize.intcomma(Place.objects.all().exclude(volume_count=0).count())
        map_ct = humanize.intcomma(Map.objects.all().exclude(loaded_by=None).count())

        ohmg_context = generate_ohmg_context(request)
        context_dict = {
            "NEWSLETTER_SLUG": newsletter_slug,
            "USER_SUBSCRIBED": user_subscribed,
            "PARTNERS": partners,
            "PLACES_CT": place_ct,
            "MAP_CT": map_ct,
            "MAPBROWSE_PARAMS": {
                "MAP_HEIGHT": "100%",
                "CONTEXT": ohmg_context,
            },
            "MAPSHOWCASE_PARAMS": {
                "CONTEXT": ohmg_context,
                "FEATURED_MAPS": featured_list,
                "PLACES_CT": place_ct,
                "MAP_CT": map_ct,
            },
            "SESSIONLIST_PARAMS": {
                "CONTEXT": ohmg_context,
                "showThumbs": True,
            },
        }

        return render(request, "index.html", context=context_dict)


class Browse(View):
    def get(self, request):
        context_dict = {
            "BROWSE_PARAMS": {
                "CONTEXT": generate_ohmg_context(request),
                "PLACES_CT": humanize.intcomma(Place.objects.all().exclude(volume_count=0).count()),
                "MAP_CT": humanize.intcomma(Map.objects.all().exclude(loaded_by=None).count()),
            }
        }
        return render(request, "frontend/browse.html", context=context_dict)


class ActivityView(View):
    def get(self, request):
        ohmg_context = generate_ohmg_context(request)
        context_dict = {
            "CONTEXT": ohmg_context,
            "SESSIONLIST_PROPS": {
                "CONTEXT": ohmg_context,
                "showThumbs": True,
                "limit": "25",
            },
        }

        return render(request, "frontend/activity.html", context=context_dict)


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

        return render(request, "frontend/article_list.html", context=context_dict)


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

        return render(request, "frontend/article.html", context=context_dict)


class Participants(View):
    def get(self, request):
        return render(
            request,
            "accounts/profiles.html",
            context={
                "PARTICIPANTS_PARAMS": {
                    "CONTEXT": generate_ohmg_context(request),
                }
            },
        )


class PageView(View):
    def get(self, request, page):
        m_date = page.date_modified.strftime("%B %d, %Y")
        context_dict = {
            "PAGE_TITLE": page.title,
            "DATE_MODIFIED": m_date if page.show_date_modified else None,
            "EXTRA_HEAD": page.extra_head,
            "MARKDOWN_CONTENT": page.content,
        }

        return render(request, "frontend/page.html", context=context_dict)
