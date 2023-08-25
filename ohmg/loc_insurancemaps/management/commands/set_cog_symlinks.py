from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from geonode.layers.models import Layer, LayerFile, UploadSession

class Command(BaseCommand):
    help = 'command to search the Library of Congress API.'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):

        cog_dir = Path(settings.MEDIA_ROOT, "cog")
        cog_dir.mkdir(exist_ok=True)

        layers = Layer.objects.all()

        for l in layers:
            path = None
            us = UploadSession.objects.filter(resource=l)
            if len(us) == 1:
                f = LayerFile.objects.filter(upload_session=us[0])
                if len(f) == 1:
                    path = f[0].file.path

            if path is not None:
                cog_path = Path(cog_dir, Path(path).name)
                cog_path.unlink(missing_ok=True)
                cog_path.symlink_to(path)
