# Source - https://stackoverflow.com/a/37988537
# Posted by Dmitry, modified by community. See post 'Timeline' for change history
# Retrieved 2026-06-05, License - CC BY-SA 4.0

from django.db import models


class Permissions(models.Model):
    """Permissions model for holding custom Django permissions objects
    that are not tied to any specific model."""

    class Meta:
        managed = False  # No database table creation or deletion  \
        # operations will be performed for this model.

        default_permissions = ()  # disable "add", "change", "delete"
        # and "view" default permissions

        permissions = (("use_helmert", "Can use Helmert transformation"),)
