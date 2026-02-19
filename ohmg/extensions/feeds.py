from django.contrib.syndication.views import Feed
from django.db.models import Q
from django.urls import reverse

from ohmg.places.models import Place
from ohmg.georeference.models import SessionBase

NUM_RSS_RETURNS = 100


class PlaceFeed(Feed):

    title = "Places"
    link = "/activity/"
    description = "Recent edits to this place"

    def get_object(self, request, place: Place) -> Place:
        # Simply pass on the place already looked up using the converter
        return place

    def items(self, item: Place):
        q = (
            # Checking this place directly
            Q(doc2__map__locales=item)
            | Q(reg2__document__map__locales=item)
            | Q(lyr2__region__document__map__locales=item)
            | Q(map__locales=item)
            # Checking this place's parents now
            | Q(doc2__map__locales__direct_parents=item)
            | Q(reg2__document__map__locales__direct_parents=item)
            | Q(lyr2__region__document__map__locales__direct_parents=item)
            | Q(map__locales__direct_parents=item)
        )
        sessions = SessionBase.objects.filter(
            q,
        ).order_by("-date_modified")[:NUM_RSS_RETURNS]
        return sessions

    def item_title(self, item: SessionBase) -> str:
        if item.doc2 is not None:
            return item.doc2.title
        elif item.reg2 is not None:
            return item.reg2.title
        elif item.lyr2 is not None:
            return item.lyr2.title
        elif item.map is not None:
            return item.map.title
        else:
            return ""

    def item_description(self, item: SessionBase) -> str:
        if item.doc2 is not None:
            init_desc = f"Document: {item.doc2}; "
        elif item.reg2 is not None:
            init_desc = f"Region: {item.reg2}; "
        elif item.lyr2 is not None:
            init_desc = f"Layer: {item.lyr2}; "
        elif item.map is not None:
            init_desc = f"Map: {item.map}; "
        else:
            init_desc = ""
        base_desc = f"{init_desc}Type: {item.type}; Stage: {item.stage}; Status: {item.status}; User: {item.user}"
        return base_desc

    def item_link(self, item: SessionBase) -> str:
        if item.doc2 is not None:
            return reverse("document_view", kwargs={"pk": item.doc2.pk})
        elif item.reg2 is not None:
            return reverse("region_view", kwargs={"pk": item.reg2.pk})
        elif item.lyr2 is not None:
            return reverse("layer_view", kwargs={"pk": item.lyr2.pk})
        elif item.map is not None:
            return reverse("map_view", kwargs={"pk": item.map.pk})
        else:
            return ""
