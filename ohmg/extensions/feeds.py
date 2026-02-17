from django.contrib.syndication.views import Feed
from django.shortcuts import get_object_or_404

from ohmg.places.models import Place


class PlaceFeed(Feed):

    def get_object(self, request, place_slug: str) -> Place:
        return get_object_or_404(Place, slug=place_slug)

    def items(self, item: Place):
        # TODO: Ultimately return SessionBase for georef/prep
        #   Get map locales, then document, layer
        #   Return last X changes sorted by date_modified
        maps = item.locales_set.all()
        return []

    def item_title(self, item: Place) -> str:
        # TODO: Not Place, more like SessionBase
        return item.name

    def item_description(self, item: Place) -> str:
        # TODO: Not Place, more like SessionBase
        return item.display_name
