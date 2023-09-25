from django.db import models
from django.urls import reverse
from django.contrib.auth.models import AbstractUser
from django.utils.functional import cached_property

from ohmg.georeference.models.sessions import SessionBase
from ohmg.georeference.models.resources import GCP

from ohmg.loc_insurancemaps.models import Volume

class User(AbstractUser):
    class Meta:
        db_table = 'auth_user'

    def __str__(self):
        return self.username

    @cached_property
    def load_ct(self):
        return Volume.objects.filter(loaded_by=self).count()

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
    def volumes(self):
        return Volume.objects.filter(loaded_by=self).order_by("city")

    @cached_property
    def profile_url(self):
        return reverse('profile_detail', args=(self.username, ))
