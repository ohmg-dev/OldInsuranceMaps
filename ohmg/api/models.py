import secrets
from django.conf import settings
from django.db import models

def generate_key():
    return secrets.token_urlsafe(16)

class Key(models.Model):

    value = models.CharField(
        primary_key=True,
        default=generate_key,
        max_length=22,
        editable=False,
    )
    account = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    active = models.BooleanField(
        default=True,
    )
    request_count = models.IntegerField(
        default=0,
        editable=False
    )

    def increment_count(self):
        self.request_count += 1
        self.save(update_fields=['request_count'])
