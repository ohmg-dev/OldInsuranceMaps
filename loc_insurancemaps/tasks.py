from celery import shared_task

from django.contrib.auth import get_user_model

from .models import Volume

@shared_task
def import_sheets_as_task(volume_id, userid):
    user = get_user_model().objects.get(pk=userid)
    volume = Volume.objects.get(pk=volume_id)
    volume.import_sheets(user=user)
