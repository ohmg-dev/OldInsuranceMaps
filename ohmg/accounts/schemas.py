from typing import List
from avatar.templatetags.avatar_tags import avatar_url
from django.urls import reverse
from ninja import (
    Schema,
)

from ohmg.api.models import Key
from ohmg.georeference.schemas import SessionSchema
from ohmg.loc_insurancemaps.models import Volume


class UserSchema(Schema):
    username: str
    profile_url: str
    psesh_ct: int
    gsesh_ct: int
    total_ct: int = 0
    gcp_ct: int
    volumes: list
    load_ct: int
    image_url: str
    email: str
    api_keys: list[str]

    @staticmethod
    def resolve_volumes(obj):
        """overrride the volumes property on the model in order to 
        create a super light-weight acquisition of volume info"""
        values = Volume.objects.filter(loaded_by=obj) \
            .order_by('city', 'year') \
            .values('identifier', 'city', 'year', 'volume_no')
        for i in values:
            i['url'] = reverse('map_summary', args=(i['identifier'], ))
            i['title'] = f"{i['city']} {i['year']}{' vol. ' + i['volume_no'] if i['volume_no'] else ''}"
        return values

    @staticmethod
    def resolve_total_ct(obj):
        return obj.psesh_ct + obj.gsesh_ct

    @staticmethod
    def resolve_image_url(obj):
        return avatar_url(obj)
    
    @staticmethod
    def resolve_api_keys(obj):
        return [i for i in Key.objects.filter(account=obj).values_list('value', flat=True)]


class UserProfileSchema(Schema):
    username: str
    sessions: List[SessionSchema]
