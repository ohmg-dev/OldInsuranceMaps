import os
import logging

from ohmg.celeryapp import app
from ohmg.georeference.models import (
    PrepSession,
    GeorefSession,
    delete_expired_session_locks,
)

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

@app.task
def delete_stale_sessions():
    delete_expired_session_locks()

@app.task
def delete_preview_vrt(base_file_path, preview_url_to_remove):

    if not preview_url_to_remove.endswith(".vrt"):
        logger.warn("will not delete non-VRT")
        return
    prev_file = os.path.basename(preview_url_to_remove)
    prev_file_path = os.path.join(os.path.dirname(base_file_path), prev_file)
    try:
        if os.path.exists(prev_file_path):
            os.remove(prev_file_path)
    except Exception as e:
        logger.warn(f"error while deleting preview VRT: {e}")
