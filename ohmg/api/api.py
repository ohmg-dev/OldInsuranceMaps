import logging
from typing import List, Optional

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.urls import reverse

from ninja import NinjaAPI, Query, FilterSchema
from ninja.pagination import paginate
from ninja.security import APIKeyHeader

from ohmg.accounts.models import User
from ohmg.accounts.schemas import UserSchema
from ohmg.api.models import Key
from ohmg.loc_insurancemaps.models import Volume
from ohmg.content.schemas import ItemListSchema
from ohmg.georeference.models import SessionBase
from ohmg.georeference.schemas import (
    FilterSessionSchema,
    SessionSchema,
)
from ohmg.places.models import Place
from ohmg.places.schemas import PlaceSchema

logger = logging.getLogger(__name__)

class ApiKey(APIKeyHeader):
    param_name = "X-API-Key"

    def authenticate(self, request, key):
        if key == settings.OHMG_API_KEY:
            return key
        elif key in Key.objects.filter(active=True).values_list('value', flat=True):
            Key.objects.get(value=key).increment_count()
            return key

# going to be useful eventually for Geo support
# https://github.com/vitalik/django-ninja/issues/335
api = NinjaAPI(
    auth=ApiKey(),
    title="OldInsuranceMaps.net API",
    version="beta",
    description="An experimental API for accessing content on "\
        "OldInsuranceMaps.net."
)


@api.get('sessions/', response=List[SessionSchema], url_name="session_list")
@paginate
def list_sessions(request, filters: FilterSessionSchema = Query(...)):
    sort = request.GET.get('sort', '')
    if sort == 'oldest_first':
        queryset = SessionBase.objects.all().order_by("date_created")
    else:
        queryset = SessionBase.objects.all().order_by("-date_created")
    queryset = filters.filter(queryset)
    return list(queryset)

@api.get('session/{session_id}/', response=SessionSchema, url_name="session_detail")
def session_details(request, session_id: int):
    return get_object_or_404(SessionBase, pk=session_id)

@api.get('users/', response=List[UserSchema], url_name="user_list")
def list_users(request):
    queryset = User.objects.all().exclude(username="AnonymousUser").order_by("username")
    return list(queryset)

class ItemFilterSchema(FilterSchema):
    """not currently used, would need to customize the fields a bit"""
    loaded_by__username: Optional[str] = None

@api.get('items/', response=List[ItemListSchema], url_name="item_list")
def list_items(request,
        # filters: ItemFilterSchema = Query(...),
        sort: str = "default",
        limit: int = None,
        loaded: bool = True,
        loaded_by: str = None,
        locale: str = None,
        locale_inclusive: bool = False,
    ):
    # overall, not really optimized. should refactor at some point...
    if sort == "load_date":
        items = Volume.objects.all().order_by('-load_date')
    else:
        items = Volume.objects.all().order_by('city', 'year')
    
    if locale:
        place = Place.objects.get(slug=locale)
        if locale_inclusive:
            if locale in ['united-states', 'mexico', 'canada', 'cuba']:
                pass
            else:
                pks = place.get_inclusive_pks()
                items = items.filter(locales__in=pks)
        else:
            items = items.filter(locales=place.pk)

    if loaded:
        items = items.exclude(loaded_by=None)
    if loaded_by:
        items = items.filter(loaded_by__username=loaded_by)

    if limit:
        items = items[:limit]
    return list(items)

@api.get('places/', response=List[PlaceSchema], url_name="place_list")
def list_places(request):
    queryset = Place.objects.all().exclude(volume_count=0).order_by('name')
    return list(queryset)

@api.get('places/geojson/', url_name="places_geojson")
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
                    'url': reverse("volume_summary", args=(volume['identifier'],)),
                })
                feature['properties']['place'] = {
                    "name": str(place),
                    "url": reverse("viewer", args=(place.slug,)),
                }

                geojson['features'].append(feature)

    return geojson

# @api.get('user/{username}/', response=UserProfileSchema)
# def user_details(request, username: str):
#     return get_object_or_404(User, username=username)
