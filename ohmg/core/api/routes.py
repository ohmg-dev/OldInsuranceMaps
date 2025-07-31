import logging
from typing import List

from django.conf import settings
from django.contrib.gis.geos import Polygon
from django.db.models import F
from django.shortcuts import get_object_or_404

from ninja import NinjaAPI, Query
from ninja.pagination import paginate
from ninja.security import APIKeyHeader

from ohmg.accounts.models import (
    User,
    APIKey,
)
from ohmg.core.models import (
    Map,
    Document,
    Region,
    Layer,
    LayerSet,
)
from ohmg.georeference.models import (
    SessionBase,
    SessionLock,
)
from ohmg.places.models import Place

from .filters import (
    FilterSessionSchema,
    FilterDocumentSchema,
    FilterAllDocumentsSchema,
    FilterRegionSchema,
)
from .schemas import (
    PlaceSchema,
    LayerSchema,
    LayerSetSchema,
    UserSchema,
    MapFullSchema,
    MapListSchema,
    SessionSchema,
    SessionLockSchema,
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
        elif key in APIKey.objects.filter(active=True).values_list("value", flat=True):
            APIKey.objects.get(value=key).increment_count()
            return key


# going to be useful eventually for Geo support
# https://github.com/vitalik/django-ninja/issues/335
beta2 = NinjaAPI(
    auth=APIKeyAuth(),
    title="OldInsuranceMaps.net API",
    version="beta2",
    description="An API for accessing content on OldInsuranceMaps.net.",
)


@beta2.get("sessions/", response=List[SessionSchema], url_name="session_list")
@paginate
def list_sessions(request, filters: FilterSessionSchema = Query(...), date_range: str = ""):
    sort = request.GET.get("sortold", "")
    sort_param = request.GET.get("sortby", "")
    sort_dir = request.GET.get("sort", "")
    if date_range:
        start, end = date_range.split(",")
        if start == end:
            sessions = SessionBase.objects.filter(date_created__contains=start)
        else:
            sessions = SessionBase.objects.filter(date_created__range=[start, end])
    else:
        sessions = SessionBase.objects.all()
    if sort_param:
        if sort_param == "user":
            sort_param = "user__username"
        if sort_param == "duration":
            sort_param = "user_input_duration"
        sort_arg = sort_param if sort_dir == "asc" else f"-{sort_param}"
        queryset = sessions.order_by(sort_arg).select_related("doc2", "reg2", "lyr2")
    elif sort == "oldest_first":
        queryset = sessions.order_by("date_created").select_related("doc2", "reg2", "lyr2")
    else:
        queryset = sessions.order_by("-date_created").select_related("doc2", "reg2", "lyr2")
    queryset = filters.filter(queryset)
    return queryset


@beta2.get("session/", response=SessionSchema, url_name="session_detail")
def session_details(request, id: int):
    return get_object_or_404(SessionBase.objects.prefetch_related(), pk=id)


@beta2.get("users/", response=List[UserSchema], url_name="user_list")
def list_users(request):
    queryset = User.objects.all().exclude(username="AnonymousUser").order_by("username")
    return queryset


# @beta2.get('map/session-summary', response=SessionSummarySchema, url_name="map_session_summary"):


@beta2.get("map/", response=MapFullSchema, url_name="map")
def get_map(request, map: str):
    return get_object_or_404(Map, pk=map)


@beta2.get("maps/", response=List[MapListSchema], url_name="map_list")
def list_maps(
    request,
    # filters: MapFilterSchema = Query(...),
    sort: str = "default",
    limit: int = None,
    loaded: bool = True,
    loaded_by: str = None,
    locale: str = None,
    locale_inclusive: bool = False,
):
    # overall, not really optimized. should refactor at some point...
    maps = Map.objects.exclude(hidden=True)
    if sort == "load_date":
        maps = maps.order_by("-load_date")
    else:
        maps = maps.order_by("title")

    if locale:
        place = Place.objects.get(slug=locale)
        if locale_inclusive:
            if locale in ["united-states", "mexico", "canada", "cuba"]:
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
    return maps


@beta2.get("layerset/", response=LayerSetSchema, url_name="layerset")
def get_layerset(
    request,
    map: str,
    category: str,
):
    return LayerSet.objects.get(category__slug=category, map_id=map)


@beta2.get("layersets/", response=List[LayerSetSchema], url_name="layersets")
def get_layersets(
    request,
    map: str,
):
    return LayerSet.objects.filter(map_id=map)


@beta2.get("place/", response=PlaceFullSchema, url_name="place")
def place(request, slug: str):
    return get_object_or_404(Place.objects.prefetch_related(), slug=slug)


@beta2.get("places/", response=List[PlaceSchema], url_name="place_list")
def list_places(request):
    queryset = Place.objects.all().exclude(volume_count=0).order_by("name")
    return queryset


@beta2.get("places/geojson/", url_name="places_geojson")
def get_places_geojson(request):
    """Generate geojson for all places with their maps."""

    place_dict = {}
    for ls in (
        LayerSet.objects.filter(category__slug="main-content")
        .prefetch_related()
        .annotate(
            locale=F("map__locales"),
            locale_name=F("map__locales__display_name"),
            locale_slug=F("map__locales__slug"),
            map_year=F("map__year"),
            map_volume_number=F("map__volume_number"),
        )
    ):
        if ls.locale and ls.extent:
            place_entry = place_dict.get(
                ls.locale_slug,
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": Polygon().from_bbox(ls.extent).centroid.coords,
                    },
                    "properties": {
                        "volumes": [],
                        "place": {
                            "url": f"/viewer/{ls.locale_slug}",
                            "display_name": ls.locale_name,
                        },
                    },
                },
            )
            year_vol = (
                f"{ls.map_year} vol. {ls.map_volume_number}"
                if ls.map_volume_number
                else ls.map_year
            )
            place_entry["properties"]["volumes"].append(
                {
                    "year": year_vol,
                    "url": f"/map/{ls.map_id}",
                }
            )
            place_dict[ls.locale_slug] = place_entry
    geojson = {
        "type": "FeatureCollection",
        "features": list(place_dict.values()),
    }
    return geojson


## DOCUMENT ROUTES
@beta2.get("document/", response=DocumentSchema, url_name="documents")
def document(request, id: int):
    return get_object_or_404(Document.objects.prefetch_related(), pk=id)


@beta2.get("documents/", response=List[DocumentSchema], url_name="documents")
def documents(request, filters: FilterDocumentSchema = Query(...)):
    queryset = Document.objects.all().prefetch_related()
    queryset = filters.filter(queryset)
    return queryset


@beta2.get("documents/all", response=List[DocumentSchema], url_name="documents")
@paginate
def documents_all(request, sort: str = None, filters: FilterAllDocumentsSchema = Query(...)):
    """Full paginated query for all documents in the database."""
    queryset = Document.objects.all().prefetch_related().order_by("map__title", "page_number")
    queryset = filters.filter(queryset)
    # if sort:
    #     queryset.order_by(sort)
    return queryset


## REGION ROUTES - WIP
@beta2.get("region/", response=RegionSchema, url_name="documents")
def region(request, id: int):
    return get_object_or_404(Region.objects.prefetch_related(), pk=id)


@beta2.get("regions/", response=List[DocumentSchema], url_name="documents")
def regions(request, filters: FilterRegionSchema = Query(...)):
    queryset = Document.objects.all().prefetch_related()
    queryset = filters.filter(queryset)
    return queryset


@beta2.get("layers/", response=List[LayerSchema], url_name="layers")
def layer(request, map: str):
    return Layer.objects.filter(region__document__map_id=map)


## SESSION LOCKS
@beta2.get("session-locks/", response=List[SessionLockSchema], url_name="session_locks")
def session_locks(request, map: str = None):
    locks = SessionLock.objects.all().prefetch_related()
    if map:
        locks = [i for i in locks if i.target.map.pk == map]
    return locks
