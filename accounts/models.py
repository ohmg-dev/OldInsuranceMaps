from django.db import models
from django.contrib.auth.models import AbstractUser

# define a custom user model here
class User(AbstractUser):
    class Meta:
        db_table = 'auth_user'

    def __str__(self):
        return self.username