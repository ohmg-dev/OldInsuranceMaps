import logging
from typing import List

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.urls import reverse

from ninja import NinjaAPI, Query
from ninja.pagination import paginate
from ninja.security import APIKeyHeader

from ohmg.accounts.models import (
    User,
    APIKey,
)
from ohmg.core.models import (
    MapGroup,
    Map,
    Document,
    Region,
    Layer,
)
from ohmg.loc_insurancemaps.models import Volume
from ohmg.georeference.models import SessionBase, LayerSet, LayerV1
from ohmg.places.models import Place

from .filters  import (
    FilterSessionSchema,
    FilterDocumentSchema,
    FilterAllDocumentsSchema,
    FilterRegionSchema,
)
from .schemas import (
    UserSchema,
    MapListSchema,
    LayerSetSchema,
    PlaceSchema,
    LayerSchema,

    SessionSchema,
    DocumentSchema,
    RegionSchema,
    PlaceFullSchema,
)

logger = logging.getLogger(__name__)


class APIKeyAuth(APIKeyHeader):
    param_name = "X-API-Key"

    def authenticate(self, request, key):
        if key == settings.OHMG_API_KEY:
            return key
        elif key in APIKey.objects.filter(active=True).values_list('value', flat=True):
            APIKey.objects.get(value=key).increment_count()
            return key

# going to be useful eventually for Geo support
# https://github.com/vitalik/django-ninja/issues/335
beta2 = NinjaAPI(
    # auth=APIKeyAuth(),
    title="OldInsuranceMaps.net API",
    version="beta2",
    description="An API for accessing content on OldInsuranceMaps.net."
)


@beta2.get('sessions/', response=List[SessionSchema], url_name="session_list")
@paginate
def list_sessions(request, filters: FilterSessionSchema = Query(...)):
    sort = request.GET.get('sort', '')
    if sort == 'oldest_first':
        queryset = SessionBase.objects.all().order_by("date_created")
    else:
        queryset = SessionBase.objects.all().order_by("-date_created")
    queryset = filters.filter(queryset)
    return list(queryset)

@beta2.get('session/', response=SessionSchema, url_name="session_detail")
def session_details(request, id: int):
    return get_object_or_404(SessionBase.objects.prefetch_related(), pk=id)

@beta2.get('users/', response=List[UserSchema], url_name="user_list")
def list_users(request):
    queryset = User.objects.all().exclude(username="AnonymousUser").order_by("username")
    return list(queryset)

# @beta2.get('map/session-summary', response=SessionSummarySchema, url_name="map_session_summary"):


@beta2.get('maps/', response=List[MapListSchema], url_name="map_list")
def list_maps(request,
        # filters: MapFilterSchema = Query(...),
        sort: str = "default",
        limit: int = None,
        loaded: bool = True,
        loaded_by: str = None,
        locale: str = None,
        locale_inclusive: bool = False,
    ):
    # overall, not really optimized. should refactor at some point...
    if sort == "load_date":
        maps = Volume.objects.all().order_by('-load_date')
    else:
        maps = Volume.objects.all().order_by('city', 'year')
    
    if locale:
        place = Place.objects.get(slug=locale)
        if locale_inclusive:
            if locale in ['united-states', 'mexico', 'canada', 'cuba']:
                pass
            else:
                pks = place.get_inclusive_pks()
                maps = maps.filter(locales__in=pks)
        else:
            maps = maps.filter(locales=place.pk)

    if loaded:
        maps = maps.exclude(loaded_by=None)
    if loaded_by:
        maps = maps.filter(loaded_by__username=loaded_by)

    if limit:
        maps = maps[:limit]
    return list(maps)

@beta2.get('annotation-set/', response=LayerSetSchema, url_name="annotation_set")
def annotation(request,
        volume: str,
        category: str,
    ):
    return LayerSet.objects.get(category__slug=category, volume_id=volume)

@beta2.get('annotation-sets/', response=List[LayerSetSchema], url_name="annotation_sets")
def annotations(request,
        volume: str,
    ):
    return LayerSet.objects.filter(volume_id=volume)


@beta2.get('place/', response=PlaceFullSchema, url_name="place")
def place(request, slug: str):
    return get_object_or_404(Place.objects.prefetch_related(), slug=slug)

@beta2.get('places/', response=List[PlaceSchema], url_name="place_list")
def list_places(request):
    queryset = Place.objects.all().exclude(volume_count=0).order_by('name')
    return list(queryset)

@beta2.get('places/geojson/', url_name="places_geojson")
def get_places_geojson(request):
    """ Still pretty hacky, but pulling this map content creation into
    a single, accessible location. """

    geojson = {
        "type": "FeatureCollection",
        "features": [],
    }

    places = Place.objects.all().exclude(volume_count=0).order_by('name')
    for place in places:

        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": None,
            },
            "properties": {
                "volumes": [],
                "place": {},
            }
        }

        ## get the centroid for the first volume that has one, then break
        for volume in Volume.objects.filter(locales__id__exact=place.id) \
                .order_by("year") \
                .values("year", "volume_no", "identifier", "extent", "layer_lookup"):
            if len(volume['layer_lookup'].values()) > 0:
                year_vol = str(volume['year'])
                if volume['volume_no'] is not None:
                    year_vol = f"{year_vol} vol. {volume['volume_no']}"

                feature['geometry']['coordinates'] = volume['extent'].centroid.coords

                feature['properties']['volumes'].append({
                    # 'title': str(volume),
                    'year': year_vol,
                    'url': reverse("map_summary", args=(volume['identifier'],)),
                })
                feature['properties']['place'] = {
                    "name": str(place),
                    "url": reverse("viewer", args=(place.slug,)),
                }

                geojson['features'].append(feature)

    return geojson


## DOCUMENT ROUTES
@beta2.get('document/', response=DocumentSchema, url_name="documents")
def document(request, id: int):
    return get_object_or_404(Document.objects.prefetch_related(), pk=id)

@beta2.get('documents/', response=List[DocumentSchema], url_name="documents")
def documents(request, filters: FilterDocumentSchema = Query(...)):

    queryset = Document.objects.all().prefetch_related()
    queryset = filters.filter(queryset)
    return queryset

@beta2.get('documents/all', response=List[DocumentSchema], url_name="documents")
@paginate
def documents_all(request, sort: str = None, filters: FilterAllDocumentsSchema = Query(...)):
    """ Full paginated query for all documents in the database. """
    queryset = Document.objects.all().prefetch_related().order_by('map__title', 'page_number')
    queryset = filters.filter(queryset)
    # if sort:
    #     queryset.order_by(sort)
    return queryset


## REGION ROUTES - WIP
@beta2.get('region/', response=RegionSchema, url_name="documents")
def region(request, id: int):
    return get_object_or_404(Region.objects.prefetch_related(), pk=id)

@beta2.get('regions/', response=List[DocumentSchema], url_name="documents")
def regions(request, filters: FilterRegionSchema = Query(...)):

    queryset = Document.objects.all().prefetch_related()
    queryset = filters.filter(queryset)
    return queryset

@beta2.get('layers/', response=List[LayerSchema], url_name="layers")
def layer(request, map: str):

    vol = Volume.objects.get(pk=map).serialize()
    layer_ids = [i['slug'] for i in vol['items']['layers']]
    layers = LayerV1.objects.filter(slug__in=layer_ids).prefetch_related('vrs')

    return layers
