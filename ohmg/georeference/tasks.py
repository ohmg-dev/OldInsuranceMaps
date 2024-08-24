import os
import logging

from ohmg.celeryapp import app
from ohmg.core.models import Layer
from ohmg.georeference.models import (
    PrepSession,
    GeorefSession,
    delete_expired_sessions,
)
from ohmg.georeference.operations.sessions import run_georeferencing, run_preparation
from ohmg.core.utils import save_file_to_object

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
def run_preparation_as_task(sessionid):
    """ This is the new way to run a prep session, not yet implemented """
    session = PrepSession.objects.get(pk=sessionid)
    run_preparation(session)

@app.task
def run_georeferencing_as_task(sessionid):
    """ This is the new way to run a georef session, not yet implemented """
    session = GeorefSession.objects.get(pk=sessionid)
    run_georeferencing(session)

@app.task
def patch_new_layer_to_session(sessionid):
    """ Use this task to patch on a new Layer after an old
    georeferencing session has completed. """
    session = GeorefSession.objects.get(pk=sessionid)
    layer = Layer.objects.create(
        created_by=session.user,
        last_updated_by=session.user,
        region=session.reg2,
    )
    layer.save()

    save_file_to_object(layer, source_object=session.lyr)

    layer.save(set_thumbnail=True, set_extent=True)
    session.lyr2 = layer
    session.save()

    # add the layer to the main-content LayerSet
    layer.layerset = layer.region.document.map.get_layerset('main-content', create=True)
    layer.save()

@app.task
def delete_expired():
    delete_expired_sessions()

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
