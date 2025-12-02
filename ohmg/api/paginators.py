from typing import Any, List

from django.contrib.auth import get_user_model
from natsort import natsorted
from ninja import Schema
from ninja.pagination import PaginationBase

from ohmg.core.models import (
    Map,
)
from ohmg.georeference.models import (
    SESSION_TYPES,
)
from ohmg.places.models import Place


class SessionPagination(PaginationBase):
    class Input(Schema):
        offset: int = 0
        limit: int = 10

    class Output(Schema):
        items: List[Any]
        count: int
        filter_items: dict

    def paginate_queryset(self, queryset, pagination: Input, **params):
        ## Crazy, this commented code was the first attempt and making a unique list of
        ## session types that only exist in the queryset, but it is way slower than the
        ## solution in use further below.
        ## The set() strategy takes ~.3 seconds, the other ~.002
        # types_unique = set(queryset.values_list("type", flat=True))
        # type_items = [{"id":i[0], "label":i[1]} for i in SESSION_TYPES if i[0] in types_unique]

        type_items = []
        for t in SESSION_TYPES:
            if queryset.filter(type=t[0]).exists():
                type_items.append({"id": t[0], "label": t[1]})

        user_ids = queryset.values_list("user", flat=True)
        users = get_user_model().objects.filter(pk__in=user_ids)
        user_items = natsorted(
            [{"id": i.username, "label": i.username} for i in users],
            key=lambda k: k["id"],
        )

        map_ids = queryset.values_list("map", flat=True)
        maps = Map.objects.filter(pk__in=map_ids)
        map_items = natsorted(
            [{"id": i[0], "label": i[1]} for i in maps.values_list("identifier", "title")],
            key=lambda k: k["label"],
        )

        filter_items = {
            "types": type_items,
            "users": user_items,
            "maps": map_items,
        }

        offset = pagination.offset
        return {
            "items": queryset[offset : offset + pagination.limit],
            "count": queryset.count(),
            "filter_items": filter_items,
        }


class MapPagination(PaginationBase):
    class Input(Schema):
        offset: int = 0
        limit: int = 10

    class Output(Schema):
        items: List[Any]
        count: int
        filter_items: dict

    def paginate_queryset(self, queryset, pagination: Input, **params):
        place_ids = set(queryset.values_list("locales", flat=True))
        places = Place.objects.filter(pk__in=place_ids)
        place_items = natsorted(
            [{"id": i.slug, "label": i.display_name} for i in places],
            key=lambda k: k["id"],
        )

        filter_items = {
            "places": place_items,
        }

        offset = pagination.offset
        return {
            "items": queryset[offset : offset + pagination.limit],
            "count": queryset.count(),
            "filter_items": filter_items,
        }


class ContributorPagination(PaginationBase):
    class Input(Schema):
        offset: int = 0
        limit: int = 50

    class Output(Schema):
        items: List[Any]
        count: int
        filter_items: dict

    def paginate_queryset(self, queryset, pagination: Input, **params):
        filter_items = {
            "maps": ["sdf"],
        }

        offset = pagination.offset
        return {
            "items": queryset[offset : offset + pagination.limit],
            "count": queryset.count(),
            "filter_items": filter_items,
        }
