from __future__ import absolute_import

import os
import dotenv
from celery import Celery

dotenv.load_dotenv()

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ohmg.settings')

app = Celery('ohmg')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings', namespace="CELERY")
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print("Request: {!r}".format(self.request))
