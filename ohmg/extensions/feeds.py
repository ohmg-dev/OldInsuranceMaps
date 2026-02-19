from django.contrib.syndication.views import Feed
from django.db.models import Q
from django.shortcuts import get_object_or_404

from ohmg.places.models import Place
from ohmg.georeference.models import SessionBase

NUM_RSS_RETURNS = 100


class PlaceFeed(Feed):

    def get_object(self, request, place: str) -> Place:
        res = get_object_or_404(Place, slug=place)
        return res

    def items(self, item: Place):
        # TODO: Ultimately return SessionBase for georef/prep
        #   Get map locales, then document, layer
        #   Return last X changes sorted by date_modified
        q = (
            # Checking this place directly
            Q(doc2__map__locales__place=item)
            | Q(reg2__document__map__locales__place=item)
            | Q(lyr2__region__document__map__locales__place=item)
            | Q(map__locales__place=item)
            # Checking this place's parents now
            | Q(doc2__map__locales__place__direct_parents=item)
            | Q(reg2__document__map__locales__place__direct_parents=item)
            | Q(lyr2__region__document__map__locales__place__direct_parents=item)
            | Q(map__locales__plac__direct_parentse=item)
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
