import logging

from celery import shared_task

from georeference.celeryapp import app
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

@app.task(
    bind=True,
    queue='cleanup',
    name='georeference.tasks.delete_expired_sessions',
)
def delete_expired(self):
    delete_expired_sessions()
