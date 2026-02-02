import logging

import humanize
from django.shortcuts import render
from django.views import View

from ohmg.api.schemas import MapListSchema2
from ohmg.conf.http import generate_ohmg_context
from ohmg.core.models import Document, Layer, Map
from ohmg.georeference.models import SessionBase
from ohmg.places.models import Place

from .models import Partner

logger = logging.getLogger(__name__)


class HomePage(View):
    def get(self, request):
        partners = [i.serialize() for i in Partner.objects.filter(published=True)]
        partners.sort(key=lambda x: x["sortorder"])

        featured_maps = Map.objects.filter(featured=True)[:5]
        featured_list = [MapListSchema2.from_orm(i).dict() for i in featured_maps]

        place_ct = humanize.intcomma(Place.objects.all().exclude(volume_count=0).count())
        map_ct = humanize.intcomma(Map.objects.all().exclude(loaded_by=None).count())

        sesh_ct = humanize.intcomma(SessionBase.objects.filter(type="g").count())

        doc_ct = humanize.intcomma(Document.objects.filter(prepared=True).count())
        lyr_ct = humanize.intcomma(Layer.objects.all().count())

        cont_ct = humanize.intcomma(
            len(set(SessionBase.objects.all().values_list("user_id", flat=True)))
        )

        ohmg_context = generate_ohmg_context(request)
        context_dict = {
            "PARTNERS": partners,
            "PLACES_CT": place_ct,
            "MAP_CT": map_ct,
            # "LATEST_MAPS": latest_maps_json,
            "MAPBROWSE_PARAMS": {
                "MAP_HEIGHT": "100%",
                "CONTEXT": ohmg_context,
            },
            "MAPSHOWCASE_PARAMS": {
                "CONTEXT": ohmg_context,
                "FEATURED_MAPS": featured_list,
                "DOC_CT": doc_ct,
                "CONT_CT": cont_ct,
                "SESH_CT": sesh_ct,
                "MAP_CT": map_ct,
                "LYR_CT": lyr_ct,
            },
            "SESSIONS_PARAMS": {
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
            "SESSIONS_PROPS": {
                "CONTEXT": ohmg_context,
                "showThumbs": True,
                "limit": "25",
            },
        }

        return render(request, "frontend/activity.html", context=context_dict)


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
