import logging
from typing import List

from django.shortcuts import get_object_or_404

from ninja.pagination import paginate
from ninja import NinjaAPI, Query

from georeference.models.sessions import SessionBase
from georeference.schemas import (
    FilterSessionSchema,
    SessionSchema,
)

logger = logging.getLogger(__name__)


# going to be useful eventually for Geo support
# https://github.com/vitalik/django-ninja/issues/335
api = NinjaAPI(
    title="OHMG API",
    version="beta",
    description="An experimental API for accessing content in this "\
        "Online Historical Map Georeferencer instance."
)


@api.get('sessions/', response=List[SessionSchema])
@paginate
def list_sessions(request, filters: FilterSessionSchema = Query(...)):
    queryset = SessionBase.objects.all().order_by("date_run")
    queryset = filters.filter(queryset)
    return list(queryset)

@api.get('session/{session_id}/', response=SessionSchema)
def session_details(request, session_id: int):
    return get_object_or_404(SessionBase, pk=session_id)