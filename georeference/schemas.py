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


class LayerSchema(Schema):
    id: int
    slug: str


class SessionSchema(Schema):

    id: int
    type: str
    user: UserSchema
    note: str = None
    doc: DocumentSchema = None
    lyr: LayerSchema = None
    data: dict


class FilterSessionSchema(FilterSchema):
    username: Optional[str] = Field(q='user__username') 
    item: Optional[List[int]] = Field(q=['doc_id', 'lyr_id'])
    type: Optional[str]
