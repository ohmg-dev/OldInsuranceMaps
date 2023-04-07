import logging
from typing import List

from django.conf import settings
from django.contrib.gis.geos import Polygon, MultiPolygon
from django.shortcuts import get_object_or_404
from django.urls import reverse

from ninja import NinjaAPI, Query
from ninja.pagination import paginate

from accounts.models import User
from accounts.schemas import UserSchema
from loc_insurancemaps.models import Volume
from content.schemas import ItemListSchema
from georeference.models.sessions import SessionBase
from georeference.schemas import (
    FilterSessionSchema,
    SessionSchema,
)
from places.models import Place
from places.schemas import PlaceSchema

logger = logging.getLogger(__name__)

def ip_whitelist(request):
    if request.META["REMOTE_ADDR"] in settings.API_IP_WHITELIST:
        return True

# going to be useful eventually for Geo support
# https://github.com/vitalik/django-ninja/issues/335
api = NinjaAPI(
    auth=ip_whitelist,
    title="OldInsuranceMaps.net API",
    version="beta",
    description="An experimental API for accessing content on "\
        "OldInsuranceMaps.net."
)


@api.get('sessions/', response=List[SessionSchema], url_name="session_list")
@paginate
def list_sessions(request, filters: FilterSessionSchema = Query(...)):
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

@api.get('items/', response=List[ItemListSchema], url_name="item_list")
def list_items(request):
    queryset = Volume.objects.all().exclude(loaded_by=None).order_by('city', 'year')
    return list(queryset)

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
