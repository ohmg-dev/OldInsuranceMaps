import os
import logging
from pathlib import Path

from django.conf import settings

from ohmg.celeryapp import app
from ohmg.core.models import LayerSet
from ohmg.georeference.models import (
    PrepSession,
    GeorefSession,
    delete_expired_session_locks,
)
from ohmg.georeference.mosaicker import Mosaicker

logger = logging.getLogger(__name__)


@app.task
def run_preparation_session(sessionid):
    session = PrepSession.objects.get(pk=sessionid)
    session.run()
    return session.pk


@app.task
def run_georeference_session(sessionid):
    session = GeorefSession.objects.get(pk=sessionid)
    session.run()
    return session.pk


@app.task()
def delete_stale_sessions():
    delete_expired_session_locks()


@app.task
def delete_preview_vrts(id):
    for p in Path(settings.MEDIA_ROOT, "vrt").glob(f"{id}*.vrt"):
        os.remove(p)


@app.task
def create_mosaic_cog(layersetid):
    try:
        layerset = LayerSet.objects.get(pk=layersetid)
    except LayerSet.DoesNotExist:
        logger.warning(f"LayerSet does not exist: {layersetid}. Cancelling mosaic creation.")
    Mosaicker().generate_cog(layerset)
