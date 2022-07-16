from celery import shared_task

from .models import Volume

@shared_task
def load_documents_as_task(volume_id):
    volume = Volume.objects.get(pk=volume_id)
    volume.load_sheet_documents()
