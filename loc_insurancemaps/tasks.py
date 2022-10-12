from celery import shared_task

from loc_insurancemaps.models import Volume
from loc_insurancemaps.management.volume import generate_mosaic_geotiff

@shared_task
def load_documents_as_task(volume_id):
    volume = Volume.objects.get(pk=volume_id)
    volume.load_sheet_documents()

@shared_task
def load_docs_as_task(volume_id):
    volume = Volume.objects.get(pk=volume_id)
    volume.load_sheet_docs()

@shared_task
def generate_mosaic_geotiff_as_task(volume_id):
    generate_mosaic_geotiff(volume_id)
