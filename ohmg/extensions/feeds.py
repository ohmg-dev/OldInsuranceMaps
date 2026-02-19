from django.contrib.syndication.views import Feed
from django.db.models import Q, QuerySet
from django.urls import reverse

from ohmg.places.models import Place
from ohmg.georeference.models import SessionBase

# Maximum number of SessionBase objects to return
NUM_RSS_RETURNS = 100


class PlaceFeed(Feed):
    """
    Given a place slug, returns a feed of SessionBase info for that place.
    """

    title = "Places"
    link = "/activity/"
    description = "Recent edits to this place"

    def get_object(self, request, place: Place) -> Place:
        """Simply pass on the place already looked up using the URL converter"""
        return place

    def items(self, item: Place) -> QuerySet[SessionBase]:
        """
        Performs a lookup to find SessionBases with a Document, Region, Layer, or Map associated with the Place.
        Also looks in direct parents of the Place.
        """
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
        sessions = (
            SessionBase.objects
            .filter(
                q,
            )
            .select_related("doc2", "reg2", "lyr2", "map", "user")
            .order_by("-date_modified")
            [:NUM_RSS_RETURNS]
        )
        return sessions

    def item_title(self, item: SessionBase) -> str:
        """
        Returns the title of the associated Document, Region, Layer, or Map
        """
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
        """
        Returns useful info of the associated Document, Region, Layer, or Map
        """
        if item.doc2 is not None:
            init_desc = item.doc2
            map = item.doc2.map
        elif item.reg2 is not None:
            init_desc = item.reg2
            map = item.reg2.document.map
        elif item.lyr2 is not None:
            init_desc = item.lyr2
            map = item.lyr2.region.document.map
        elif item.map is not None:
            init_desc = item.map
            map = item.map
        else:
            init_desc = ""
            map = ""
        map_desc = map.title
        if map.volume_number is not None:
            map_desc += f" | {map.volume_number}"
        session_type = "Georef" if item.type == "g" else "Prep"
        base_desc = (f"ID: {item.pk}; "
                     f"Type: {session_type}; "
                     f"User: {item.user}; "
                     f"Map: {map_desc}; "
                     f"Resource: {init_desc}; "
                     f"Stage: {item.stage}; "
                     f"Result: {item.note}; "
                     f"Duration: {item.user_input_duration}; "
                     f"Date: {item.date_modified.strftime('%Y-%m-%d %H:%M:%S')}")
        return base_desc

    def item_link(self, item: SessionBase) -> str:
        """
        Returns a direct link to the associated Document, Region, Layer, or Map.
        """
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
