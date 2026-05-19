import logging
import os
import shutil
from pathlib import Path

from django.conf import settings

from ohmg.conf.celery import app
from ohmg.core.models import LayerSet
from ohmg.core.utils.s3 import get_boto3_s3_client

from .models import (
    GeorefSession,
    PrepSession,
)
from .sessions import delete_expired_session_locks

logger = logging.getLogger(__name__)


@app.task
def run_preparation_session(sessionid):
    session = PrepSession.objects.get(pk=sessionid)
    session.run()
    return session.pk


@app.task
def bulk_run_preparation_sessions(sessionids):
    for sessionid in sessionids:
        session = PrepSession.objects.get(pk=sessionid)
        session.run()
    return sessionids


@app.task
def run_georeference_session(sessionid):
    session = GeorefSession.objects.get(pk=sessionid)
    session.run()
    return session.pk


@app.task
def delete_stale_sessions():
    delete_expired_session_locks()


@app.task
def delete_preview_vrts(id):
    for p in Path(settings.MEDIA_ROOT, "vrt").glob(f"{id}*.vrt"):
        os.remove(p)


@app.task
def create_mosaic_cog(layersetid):
    from ohmg.georeference.mosaicker import Mosaicker

    try:
        layerset = LayerSet.objects.get(pk=layersetid)
    except LayerSet.DoesNotExist:
        logger.warning(f"LayerSet does not exist: {layersetid}. Cancelling mosaic creation.")
    m = Mosaicker()
    m.generate_cog(layerset)
    m.cleanup_files()


@app.task
def create_mosaic_tileset(layersetid):
    from ohmg.georeference.mosaicker import Mosaicker

    try:
        layerset = LayerSet.objects.get(pk=layersetid)
    except LayerSet.DoesNotExist:
        logger.warning(f"LayerSet does not exist: {layersetid}. Cancelling mosaic creation.")
    m = Mosaicker()
    m.generate_xyz_tiles(layerset)
    m.cleanup_files()


@app.task
def cleanup_existing_tileset(prefix):
    logger.info(f"deleting existing tileset {prefix}")
    if settings.ENABLE_S3_STORAGE:
        s3 = get_boto3_s3_client()
        response = s3.list_objects_v2(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Prefix=prefix)
        logger.info(f"deleting {len(response['Contents'])} tiles")
        for object in response["Contents"]:
            s3.delete_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=object["Key"])
    else:
        try:
            shutil.rmtree(
                Path(settings.MEDIA_ROOT, prefix),
                ignore_errors=True,
            )
        except FileNotFoundError:
            pass
