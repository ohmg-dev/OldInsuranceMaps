from typing import List, Any

from natsort import natsorted

from django.contrib.auth import get_user_model

from ninja.pagination import PaginationBase
from ninja import Schema

from ohmg.core.models import (
    Map,
)
from ohmg.georeference.models import (
    SESSION_TYPES,
)


class SessionPagination(PaginationBase):
    class Input(Schema):
        offset: int
        limit: int

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

        ## TODO: Add .map to SessionBase and auto-set it based on the doc2, reg2, or lyr2
        ## attributes. Then, implement a dynamic list of maps here.
        maps = Map.objects.exclude(hidden=True).order_by("title")
        map_items = [{"id": i[0], "label": i[1]} for i in maps.values_list("identifier", "title")]

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
