
import os
from osgeo import gdal
import json

from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.contrib.contenttypes.models import ContentType

from geonode.documents.models import Document as GNDocument
from geonode.layers.models import Layer as GNLayer

from georeference.models.resources import (
    Document,
    Layer,
    DocumentLink,
    SplitDocumentLink,
    GeoreferencedDocumentLink,
    ItemBase,
)
from georeference.models.sessions import SessionBase
from georeference.proxy_models import LayerProxy, DocumentProxy

from loc_insurancemaps.models import Volume, Sheet

class Command(BaseCommand):
    help = 'command to search the Library of Congress API.'

    def add_arguments(self, parser):

        parser.add_argument(
            "--docs",
            action="store_true",
            help="",
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            help="",
        )
        parser.add_argument(
            "--reset-all",
            action="store_true",
            help="",
        )
        parser.add_argument(
            "--links",
            action="store_true",
            help="",
        )
        parser.add_argument(
            "--layers",
            action="store_true",
            help="",
        )
        parser.add_argument(
            "--volumes",
            action="store_true",
            help="",
        )

    def handle(self, *args, **options):

        def translate_status(status):
            if status in ["trimming", "trimmed"]:
                status = "georeferenced"
            return status

        if options["reset_all"]:

            for s in SessionBase.objects.all():
                s.doc = None
                s.lyr = None
                s.save()
            model_list = [
                ItemBase,
                Document,
                Layer,
                DocumentLink,
            ]

            for model in model_list:
                objs = model.objects.all()
                print(f"removing {objs.count()} {model.__name__} objects")
                objs.delete()
            exit()

        gn_docs = GNDocument.objects.filter(title__contains="Nora Springs")
        gn_layers = GNLayer.objects.filter(title__contains="Nora Springs")

        if options['reset']:
            DocumentLink.objects.all().delete()

        # iterate Documents and create new instances for them.
        if options['docs']:
            if options['reset']:
                Document.objects.all().delete()
            for d in gn_docs:

                try:
                    newdoc = Document.objects.get(pk=d.pk)
                except Document.DoesNotExist:
                    newdoc = Document.objects.create(pk=d.pk)
                
                dp = DocumentProxy(d)
                newdoc.title = dp.title
                newdoc.status = translate_status(dp.status)
                newdoc.date = d.date
                newdoc.owner = d.owner
                # save to set the slug
                newdoc.save()
                if d.doc_file:
                    orig_path = d.doc_file.path
                    ext = os.path.splitext(orig_path)[1]
                    newfile = f"{newdoc.slug}{ext}"
                    with open(orig_path, "rb") as f:
                        newdoc.file.save(newfile, File(f))
                newdoc.save()

                for s in Sheet.objects.filter(document=d):
                    s.doc = newdoc
                    s.save()

                for p in SessionBase.objects.filter(document=d):
                    p.doc = newdoc
                    p.save()

        if options['layers']:

            if options['reset']:
                Layer.objects.all().delete()
            for l in gn_layers:

                try:
                    lyr = Layer.objects.get(pk=l.pk)
                except Layer.DoesNotExist:
                    lyr = Layer.objects.create(pk=l.pk)

                lp = LayerProxy(l)
                lyr.title = lp.title
                lyr.status = translate_status(lp.status)
                lyr.date = l.date
                lyr.owner = l.owner
                lyr.save()
                lyr_file = lp.get_layer_file()
                if lyr_file:
                    fname = os.path.basename(lyr_file.path)
                    lyr.file.save(fname, lyr_file)

                for p in SessionBase.objects.filter(layer=l):
                    p.lyr = lyr

        if options['links']:
            doc_ct = ContentType.objects.get(app_label="georeference", model="document")
            for sl in SplitDocumentLink.objects.all():
                if Document.objects.filter(pk=sl.document.pk).exists():
                    if Document.objects.filter(pk=sl.object_id).exists():
                        DocumentLink.objects.create(
                            source=Document.objects.get(pk=sl.document.pk),
                            target_type=doc_ct,
                            target_id=sl.object_id,
                            link_type="split",
                        )

            lyr_ct = ContentType.objects.get(app_label="georeference", model="layer")
            for sl in GeoreferencedDocumentLink.objects.all():
                if Document.objects.filter(pk=sl.document.pk).exists():
                    if Layer.objects.filter(pk=sl.object_id).exists():
                        DocumentLink.objects.create(
                            source=Document.objects.get(pk=sl.document.pk),
                            target_type=lyr_ct,
                            target_id=sl.object_id,
                            link_type="georeference",
                        )

        if options['volumes']:
            vols = Volume.objects.filter(pk="sanborn02775_005")
            for v in vols:
                old_main = [i for i in v.ordered_layers["layers"] if i.startswith("geonode:")]
                old_index = [i for i in v.ordered_layers["index_layers"] if i.startswith("geonode:")]

                v.sorted_layers["main"] = list(set([i.replace("geonode:", "") for i in old_main]))
                v.sorted_layers["key_map"] = list(set([i.replace("geonode:", "") for i in old_index]))
                v.save()