import os
import glob

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.core.files.uploadedfile import SimpleUploadedFile

from geonode.documents.models import Document

class Command(BaseCommand):
    help = 'creates Documents from all of the JPEG files in the given directory.'

    def add_arguments(self, parser):
        parser.add_argument(
            "--dir",
            help="directory where the image files are stored",
        )

    def handle(self, *args, **options):

        if options["dir"] is not None:
            imgdir = options["dir"]
        else:
            appdir = os.path.dirname(os.path.dirname((os.path.dirname(__file__))))
            imgdir = os.path.join(appdir, "fixtures", "img", "coushatta")

        print(imgdir)
        for imgpath in glob.glob(imgdir + "/*.jpg"):
            with open(imgpath, 'rb') as openf:
                imgdata = openf.read()

            f = SimpleUploadedFile(
                os.path.basename(imgpath),
                imgdata,
                'image/jpg')

            superuser = get_user_model().objects.get(username='admin')
            c = Document.objects.create(
                doc_file=f,
                owner=superuser,
                title=f.name)
            c.set_default_permissions()
