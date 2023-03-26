from django.db import models
from django.urls import reverse
from django.contrib.auth.models import AbstractUser

from georeference.models.sessions import SessionBase
from georeference.models.resources import GCP

from loc_insurancemaps.models import Volume

class User(AbstractUser):
    class Meta:
        db_table = 'auth_user'

    def __str__(self):
        return self.username

    def serialize(self):

        psesh_ct = SessionBase.objects.filter(user=self, type="p").count()
        gsesh_ct = SessionBase.objects.filter(user=self, type="g").count()
        total = psesh_ct + gsesh_ct
        volumes = Volume.objects.filter(loaded_by=self).order_by("city")
        load_ct = volumes.count()
        load_volumes = [
            {
                "city": v.city,
                "year": v.year,
                "url": f"/loc/{v.identifier}",
                "volume_no": v.volume_no,
                "title": f"{v.city} {v.year}{' vol. ' + v.volume_no if v.volume_no else ''}"
            } for v in volumes
        ]

        return {
            # "avatar": p_data['avatar'],
            "avatar": "",
            "username": self.username,
            "profile_url": reverse('profile_detail', args=(self.username, )),
            "load_ct": load_ct,
            "psesh_ct": psesh_ct,
            "gsesh_ct": gsesh_ct,
            "total_ct": total,
            "volumes": load_volumes,
            "gcp_ct": GCP.objects.filter(created_by=self).count()
        }
