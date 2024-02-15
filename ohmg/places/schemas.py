from django.urls import reverse
from ninja import (
    Schema,
    Field
)

from ohmg.loc_insurancemaps.models import Volume

class PlaceSchema(Schema):
    """ very lightweight serialization of a Place with its Maps"""

    name: str = Field(..., alias="__str__")
    maps: list
    url: str

    @staticmethod
    def resolve_maps(obj):
        values = Volume.objects.filter(locales__id__exact=obj.id) \
            .order_by('year') \
            .values('identifier', 'year', 'volume_no')
        for i in values:
            i['url'] = reverse('map_summary', args=(i['identifier'], ))
        return values

    @staticmethod
    def resolve_url(obj):
        return reverse('viewer', args=(obj.slug, ))
