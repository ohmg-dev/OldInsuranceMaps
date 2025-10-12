import secrets
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils.functional import cached_property

from ohmg.core.models import Map
from ohmg.georeference.models import SessionBase, GCP


class User(AbstractUser):
    class Meta:
        db_table = "auth_user"

    def __str__(self):
        return self.username

    @cached_property
    def load_ct(self):
        return Map.objects.filter(loaded_by=self).count()

    @cached_property
    def psesh_ct(self):
        return SessionBase.objects.filter(user=self, type="p").count()

    @cached_property
    def gsesh_ct(self):
        return SessionBase.objects.filter(user=self, type="g").count()

    @cached_property
    def gcp_ct(self):
        return GCP.objects.filter(created_by=self).count()

    @cached_property
    def maps(self):
        return Map.objects.filter(loaded_by=self).order_by("title")

    @cached_property
    def profile_url(self):
        return reverse("profile_detail", args=(self.username,))

    @cached_property
    def api_keys(self):
        return [i for i in APIKey.objects.filter(account=self).values_list("value", flat=True)]


def generate_key():
    return secrets.token_urlsafe(16)


class APIKey(models.Model):
    class Meta:
        verbose_name = "API Key"

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
    request_count = models.IntegerField(default=0, editable=False)

    def increment_count(self):
        self.request_count += 1
        self.save(update_fields=["request_count"])
