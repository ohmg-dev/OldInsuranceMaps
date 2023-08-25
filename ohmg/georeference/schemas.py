from typing import List, Optional

from django.urls import reverse
from ninja import (
    FilterSchema,
    Field,
    Schema,
)


class UserSchema(Schema):
    username: str
    profile_url: str

    @staticmethod
    def resolve_profile_url(obj):
        return reverse('profile_detail', args=(obj.username, ))


class DocumentSchema(Schema):
    id: int
    title: str
    detail_url: str
    thumb_url: str = ''

    @staticmethod
    def resolve_thumb_url(obj):
        if obj.thumbnail:
            return obj.thumbnail.url

    @staticmethod
    def resolve_detail_url(obj):
        return reverse("resource_detail", args=(obj.pk, ))


class LayerSchema(Schema):
    id: int
    title: str
    slug: str
    detail_url: str
    thumb_url: str = ''

    @staticmethod
    def resolve_thumb_url(obj):
        if obj.thumbnail:
            return obj.thumbnail.url
    
    @staticmethod
    def resolve_detail_url(obj):
        return reverse("resource_detail", args=(obj.pk, ))


class SessionSchema(Schema):

    id: int
    type: str
    user: UserSchema
    note: str = None
    doc: DocumentSchema = None
    lyr: LayerSchema = None
    status: str
    data: dict
    user_input_duration: int = None
    date_created: str = None

    @staticmethod
    def resolve_date_created(obj):
        return obj.date_created.strftime("%Y-%m-%d")

class FilterSessionSchema(FilterSchema):
    username: Optional[str] = Field(q='user__username') 
    item: Optional[List[int]] = Field(q=['doc_id', 'lyr_id'])
    type: Optional[str]
