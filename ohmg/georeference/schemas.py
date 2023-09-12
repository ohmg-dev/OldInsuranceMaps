from datetime import datetime
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
    # resource_id = int
    doc: DocumentSchema = None
    lyr: LayerSchema = None
    status: str
    stage: str
    data: dict
    user_input_duration: int = None
    date_created: dict = None

    @staticmethod
    def resolve_date_created(obj):
        d = {
            'date': obj.date_created.strftime("%Y-%m-%d"),
            'relative': ''
        }
        diff = datetime.now() - obj.date_created

        if diff.days > 0:
            n, u = diff.days, 'day'
        else:
            seconds = diff.total_seconds()
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            seconds = seconds % 60
            if hours > 0:
                n, u = hours, "hour"
            elif minutes > 0:
                n, u = minutes, "minute"
            else:
                n, u = seconds, "second"
        n = int(n)
        d['relative'] = f"{n} {u}{'' if n == 1 else 's'} ago"
        return d

class FilterSessionSchema(FilterSchema):
    username: Optional[str] = Field(q='user__username') 
    item: Optional[List[int]] = Field(q=['doc_id', 'lyr_id'])
    resource: Optional[List[int]] = Field(q=['doc_id__in', 'lyr_id__in'])
    type: Optional[str]
