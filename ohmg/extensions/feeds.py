from django.contrib.syndication.views import Feed
from django.db.models import Q
from django.shortcuts import get_object_or_404

from ohmg.places.models import Place
from ohmg.georeference.models import SessionBase

NUM_RSS_RETURNS = 100


class PlaceFeed(Feed):

    title = "Places"
    link = "/latestplaces/"
    description = "Recent edits to this place"

    def get_object(self, request, place: Place) -> Place:
        # Simply pass on the place already looked up using the converter
        return place

    def items(self, item: Place):
        # TODO: Ultimately return SessionBase for georef/prep
        #   Get map locales, then document, layer
        #   Return last X changes sorted by date_modified
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

    def item_title(self, item: Place) -> str:
        # TODO: Not Place, more like SessionBase
        return item.name

    def item_description(self, item: Place) -> str:
        # TODO: Not Place, more like SessionBase
        return item.display_name
