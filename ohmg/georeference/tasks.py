import logging
import os
import shutil
from pathlib import Path

from django.conf import settings

from ohmg.conf.celery import app
from ohmg.core.models import LayerSet
from ohmg.core.utils.s3 import get_boto3_s3_client

logger = logging.getLogger(__name__)


@app.task
def run_preparation_session(sessionid):
    from .models import PrepSession

    session = PrepSession.objects.get(pk=sessionid)
    session.run()
    return session.pk


@app.task
def bulk_run_preparation_sessions(sessionids):
    from .models import PrepSession

    for sessionid in sessionids:
        session = PrepSession.objects.get(pk=sessionid)
        session.run()
    return sessionids


@app.task
def run_georeference_session(sessionid):
    from .models import GeorefSession

    session = GeorefSession.objects.get(pk=sessionid)
    session.run()
    return session.pk


@app.task
def delete_stale_sessions():
    from .sessions import delete_expired_session_locks

    delete_expired_session_locks()


@app.task
def delete_preview_vrts(id):
    for p in Path(settings.MEDIA_ROOT, "vrt").glob(f"{id}*.vrt"):
        os.remove(p)


@app.task
def create_mosaic_cog(layersetid: int, jobid: int | None = None):
    from .models import Job
    from .mosaicker import Mosaicker

    logger.debug("begin create mosaic task")
    try:
        layerset = LayerSet.objects.get(pk=layersetid)
    except LayerSet.DoesNotExist:
        logger.warning(f"LayerSet does not exist: {layersetid}. Cancelling mosaic creation.")
    try:
        m = Mosaicker()
        success = True
        message = m.generate_cog(layerset)
        m.cleanup_files()
    except Exception as e:
        success = False
        message = e

    if jobid:
        Job.objects.get(pk=jobid).end(success=success, message=message)


@app.task
def create_mosaic_tileset(layersetid: int, jobid: int | None = None):
    from .models import Job
    from .mosaicker import Mosaicker

    try:
        layerset = LayerSet.objects.get(pk=layersetid)
    except LayerSet.DoesNotExist:
        logger.warning(f"LayerSet does not exist: {layersetid}. Cancelling mosaic creation.")
    try:
        m = Mosaicker()
        success = True
        message = m.generate_tileset(layerset)
        m.cleanup_files()
    except Exception as e:
        success = False
        message = e

    if jobid:
        Job.objects.get(pk=jobid).end(success=success, message=message)


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


@app.task
def run_queued_mosaic_jobs():
    from ohmg.georeference.models import Job

    max_jobs_ct = settings.MAX_CONCURRENT_MOSAIC_JOBS

    mosaic_jobs = Job.objects.filter(operation__in=["layerset_to_cog", "layerset_to_xyz"])

    ## if there are already max mosaic jobs running, don't start another one
    running_jobs_ct = mosaic_jobs.filter(stage="running").count()
    spots_left = max_jobs_ct - running_jobs_ct
    if spots_left:
        queued_jobs = mosaic_jobs.filter(stage="queued").order_by("date_queued")
        for job in queued_jobs[:spots_left]:
            logger.info(f"starting queued job {job.pk}: {job.operation}, {job.target}")
            job.run()
