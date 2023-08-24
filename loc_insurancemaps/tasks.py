from celery import shared_task

from ohmg.content.models import Item
from loc_insurancemaps.models import Volume

@shared_task
def load_docs_as_task(volume_id):
    volume = Volume.objects.get(pk=volume_id)
    volume.load_sheet_docs()

@shared_task
def generate_mosaic_cog_task(volume_id):
    item = Item(volume_id)
    item.generate_mosaic_cog()

@shared_task
def generate_mosaic_json_task(volume_id, trim_all=False):
    item = Item(volume_id)
    item.generate_mosaic_json(trim_all=trim_all)
