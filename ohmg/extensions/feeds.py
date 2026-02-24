from datetime import datetime

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

    # TODO: If we ever have a activity page solely for a Place or Map, this can be dynamic.
    link = "/activity/"
item_guid_is_permalink = False
    def __init__(self):
        """Needed to create absolute URL for the item author's profile page."""
        self.request = None

    def get_object(self, request, place: Place) -> Place:
        """
        Simply pass on the place already looked up using the URL converter
        Save request for later.
        """
        self.request = request
        return place

    def title(self, item: Place) -> str:
        """
        Returns the title of the Place
        """
        title = f"Georeferencing and preparation activity for {item.display_name}"
        return title

    def description(self, place: Place) -> str:
        """
        Returns the description of the Place
        """
        description = f"The last {NUM_RSS_RETURNS} (or less) georeference or preparations for {place.display_name}."
        return description


    def items(self, item: Place) -> QuerySet[SessionBase]:
        """
        Performs a lookup to find SessionBases with a Document, Region, Layer, or Map associated with the Place.
        Also looks in direct parents of the Place.
        """
        all_places = item.get_inclusive_pks()
        # Very similar to get_inclusive_pks, except picks up volume_count_inclusive = 0
        descendants = item.get_descendants()
        while descendants:
            all_places.extend(descendants)
            new_descendants = []
            for d in descendants:
                new_descendants.extend(d.get_descendants())
            descendants = new_descendants
        q = (
            Q(doc2__map__locales__in=all_places)
            | Q(reg2__document__map__locales__in=all_places)
            | Q(lyr2__region__document__map__locales__in=all_places)
            | Q(map__locales__in=all_places)
        )
        sessions = (
            SessionBase.objects
            .filter(map__locales__in=all_places)
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
                     f"User: {item.user.username}; "
                     f"Map: {map_desc}; "
                     f"Resource: {init_desc}; "
                     f"Stage: {item.stage}; "
                     f"Result: {item.note}; "
                     f"Duration: {item.user_input_duration}; "
                     f"Date: {item.date_modified.strftime('%Y-%m-%d %H:%M:%S')}")
        return base_desc
    def item_guid(self, obj):
        """
        Set a random UUID for each item, so that the exact same session can appear in
        multiple feeds if necessary and won't be filtered by RSS clients.
        """
        return str(uuid.uuid4())
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

    def item_author_name(self, item: SessionBase) -> str:
        """
        Returns the username of the SessionBase.
        """
        return item.user.username

    def item_author_link(self, item: SessionBase) -> str:
        """
        Returns a link to the user's profile page.

        NOTE: The RSS feed (class Rss201rev2Feed) does not include this attribute. Only author name and email
        See https://cyber.harvard.edu/rss/rss.html#ltauthorgtSubelementOfLtitemgt
        """
        user_url = reverse("profile_detail", kwargs={"username": item.user.username})
        full_url = self.request.build_absolute_uri(user_url)
        return full_url

    def item_pubdate(self, item: SessionBase) -> datetime:
        return item.date_created
