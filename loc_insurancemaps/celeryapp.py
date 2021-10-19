from __future__ import absolute_import

import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'loc_insurancemaps.settings')

app = Celery('loc_insurancemaps')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings', namespace="CELERY")
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print("Request: {!r}".format(self.request))
