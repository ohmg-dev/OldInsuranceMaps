import os
import glob

from django.contrib.auth import get_user_model
from django.core import management
from django.core.management.base import BaseCommand, CommandError
from django.core.files.uploadedfile import SimpleUploadedFile

from geonode.base.models import ThesaurusKeyword
from geonode.documents.models import Document
from geonode.layers.models import Layer

from georeference import models as gmodels

class Command(BaseCommand):
    help = 'command to search the Library of Congress API.'

    def add_arguments(self, parser):
        parser.add_argument(
            "operation",
            choices=["reset-all"],
            help="",
        )

        parser.add_argument(
            "--test-data",
            action="store_true",
            help="",
        )

    def handle(self, *args, **options):

        if options["operation"] == "reset-all":
            model_list = [
                Document,
                Layer,
                gmodels.GCP,
                gmodels.GCPGroup,
                gmodels.GeoreferenceSession,
                gmodels.SplitSession,
                gmodels.Segmentation,
                gmodels.SplitDocumentLink,
                gmodels.LayerMask,
                gmodels.MaskSession,
            ]

            for model in model_list:
                objs = model.objects.all()
                print(f"removing {objs.count()} {model.__name__} objects")
                objs.delete()

        if options["operation"] == "load-documents" or options["test_data"] is True:

            appdir = os.path.dirname(os.path.dirname((os.path.dirname(__file__))))
            imgdir = os.path.join(appdir, "tests", "data", "image_files")

            for imgpath in glob.glob(imgdir + "/*.jpg"):
                with open(imgpath, 'rb') as openf:
                    imgdata = openf.read()

                f = SimpleUploadedFile(
                    os.path.basename(imgpath),
                    imgdata,
                    'image/jpg')

                title = f.name.replace(".jpg", "")

                superuser = get_user_model().objects.get(username='admin')
                c = Document.objects.create(
                    doc_file=f,
                    owner=superuser,
                    title=title
                )
                c.set_default_permissions()

                tk = ThesaurusKeyword.objects.get(about="unprepared")
                c.tkeywords.add(tk)
