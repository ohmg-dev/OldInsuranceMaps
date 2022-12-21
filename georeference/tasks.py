import logging
from celery import shared_task

from georeference.models.sessions import (
    PrepSession,
    GeorefSession,
    delete_expired_sessions,
)

logger = logging.getLogger(__name__)

@shared_task
def run_preparation_session(sessionid):
    session = PrepSession.objects.get(pk=sessionid)
    session.run()

@shared_task
def run_georeference_session(sessionid):
    session = GeorefSession.objects.get(pk=sessionid)
    session.run()

@shared_task
def delete_expired():
    delete_expired_sessions()
