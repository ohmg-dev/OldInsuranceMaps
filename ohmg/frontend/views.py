import logging
import xml.etree.ElementTree as ET

import humanize
import requests
from django.shortcuts import render
from django.views import View

from ohmg.api.schemas import MapListSchema2, SessionSchema
from ohmg.core.models import Document, Layer, Map
from ohmg.georeference.models import GCP, SessionBase
from ohmg.places.models import Place

from .models import Partner

logger = logging.getLogger(__name__)


class HomePage(View):
    def get(self, request):
        partners = [i.serialize() for i in Partner.objects.filter(published=True)]
        partners.sort(key=lambda x: x["sortorder"])

        featured_maps = Map.objects.filter(featured_rank__gt=0).order_by("featured_rank")
        featured_list = [MapListSchema2.from_orm(i).dict() for i in featured_maps]

        latest_maps = Map.objects.filter(loaded_by__isnull=False).order_by("-load_date")[:5]
        latest_list = [MapListSchema2.from_orm(i).dict() for i in latest_maps]

        latest_activity = SessionBase.objects.all().order_by("-date_created")[:5]
        activity_list = [SessionSchema.from_orm(i) for i in latest_activity]

        place_ct = humanize.intcomma(Place.objects.all().exclude(volume_count=0).count())
        map_ct = humanize.intcomma(Map.objects.all().exclude(loaded_by=None).count())

        sesh_ct = humanize.intcomma(SessionBase.objects.filter(type="g").count())

        doc_ct = humanize.intcomma(Document.objects.filter(prepared=True).count())
        lyr_ct = humanize.intcomma(Layer.objects.all().count())
        gcp_ct = humanize.intcomma(GCP.objects.all().count())

        cont_ct = humanize.intcomma(
            len(set(SessionBase.objects.all().values_list("user_id", flat=True)))
        )

        ## get blog posts to display on home page
        blog_posts = []
        try:
            response = requests.get("https://blog.oldinsurancemaps.net/feed.xml")
            root = ET.fromstring(response.content)
            for n, item in enumerate(root.findall(".//item"), start=1):
                if item.find("pubDate") is not None:
                    datestr = item.find("pubDate").text
                    datestr = datestr[:-15]
                else:
                    datestr = "No date"
                blog_posts.append(
                    {
                        "title": item.find("title").text
                        if item.find("title") is not None
                        else "No Title",
                        "link": item.find("link").text
                        if item.find("link") is not None
                        else "No Link",
                        "date": datestr,
                    }
                )
                if n == 5:
                    break
        except Exception as e:
            logger.warning("Error fetching blog posts:", e)

        context_dict = {
            "PARTNERS": partners,
            "PLACES_CT": place_ct,
            "MAP_CT": map_ct,
            "MAPBROWSE_PARAMS": {
                "MAP_HEIGHT": "100%",
                "CONTEXT": request.ohmg_context,
            },
            "FEATURED_MAPS": featured_list,
            "LATEST_MAPS": latest_list,
            "RECENT_ACTIVITY": activity_list,
            "DOC_CT": doc_ct,
            "CONT_CT": cont_ct,
            "SESH_CT": sesh_ct,
            "LYR_CT": lyr_ct,
            "GCP_CT": gcp_ct,
            "BLOG_POSTS": blog_posts,
        }

        return render(request, "index.html", context=context_dict)


class Browse(View):
    def get(self, request):
        context_dict = {
            "BROWSE_PARAMS": {
                "CONTEXT": request.ohmg_context,
                "PLACES_CT": humanize.intcomma(Place.objects.all().exclude(volume_count=0).count()),
                "MAP_CT": humanize.intcomma(Map.objects.all().exclude(loaded_by=None).count()),
            }
        }
        return render(request, "frontend/browse.html", context=context_dict)


class ActivityView(View):
    def get(self, request):
        context_dict = {
            "SESSIONS_PROPS": {
                "CONTEXT": request.ohmg_context,
                "showThumbs": True,
                "limit": "25",
            },
        }

        return render(request, "frontend/activity.html", context=context_dict)


class JobsView(View):
    def get(self, request):
        context_dict = {
            "JOBS_PROPS": {
                "CONTEXT": request.ohmg_context,
                "showThumbs": True,
                "limit": "25",
            },
        }

        return render(request, "frontend/jobs.html", context=context_dict)


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
