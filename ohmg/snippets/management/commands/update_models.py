
import os
import json

from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.contrib.contenttypes.models import ContentType

from geonode.documents.models import Document as GNDocument
from geonode.layers.models import Layer as GNLayer

from ohmg.georeference.models.resources import (
    Document,
    Layer,
    DocumentLink,
    SplitDocumentLink,
    GeoreferencedDocumentLink,
    ItemBase,
    GCPGroup,
)
from ohmg.georeference.models.sessions import SessionBase
try:
    from ohmg.georeference.proxy_models import LayerProxy, DocumentProxy
except ImportError:
    print("DocumentProxy and LayerProxy cannot be imported, proceeding without!")

from ohmg.loc_insurancemaps.models import Volume, Sheet

class Command(BaseCommand):
    help = 'A one-time migration command to copy the contents from GeoNode Document '\
        'and Layer instances into the new analogous models in the georeference app. '\
        'Also, all Volume lookups are updated to use the new serialized instances.' 

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
            "--reset-links",
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
        parser.add_argument(
            "--all",
            action="store_true",
            help="",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="",
            default=False,
        )
        parser.add_argument(
            "-c",
            "--city",
        )

    def _translate_status(self, status):
        if status in ["trimming", "trimmed"]:
            status = "georeferenced"
        return status

    def handle(self, *args, **options):

        self.verbosity = options['verbosity']
        self.dry_run = options['dry_run']

        if options["reset_all"]:
            self.reset_all()
            exit()

        if options['docs'] or options['all']:
            self.transfer_documents(city=options['city'])

        if options['layers'] or options['all']:
            self.transfer_layers(city=options['city'])

        if options['links'] or options['all']:
            self.create_new_links()

        if options['volumes'] or options['all']:
            self.update_volumes(city=options['city'])

    def reset_all(self):

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
            if self.dry_run is False:
                objs.delete()
            else:
                print("(dry run)")

    def transfer_documents(self, city=None):

        if city is not None:
            gn_docs = GNDocument.objects.filter(title__contains=city)
        else:
            gn_docs = GNDocument.objects.all()
        
        print(f"{gn_docs.count()} documents to transfer")

        for d in gn_docs:
            if self.verbosity >= 2:
                print(d)

            if self.dry_run is False:
                try:
                    newdoc = Document.objects.get(pk=d.pk)
                except Document.DoesNotExist:
                    newdoc = Document.objects.create(pk=d.pk)
                
                dp = DocumentProxy(d)
                newdoc.title = dp.title
                newdoc.status = self._translate_status(dp.status)
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

                for g in GCPGroup.objects.filter(document=d):
                    g.doc = newdoc
                    g.save()

    def transfer_layers(self, city=None):

        if city is not None:
            gn_layers = GNLayer.objects.filter(title__contains=city)
        else:
            gn_layers = GNLayer.objects.all()

        print(f"{gn_layers.count()} layers to transfer")

        for l in gn_layers:
            if self.verbosity >= 2:
                print(l)
            if not self.dry_run:

                try:
                    lyr = Layer.objects.get(pk=l.pk)
                except Layer.DoesNotExist:
                    lyr = Layer.objects.create(pk=l.pk)

                lp = LayerProxy(l)
                lyr.title = lp.title
                lyr.status = self._translate_status(lp.status)
                lyr.date = l.date
                lyr.owner = l.owner
                lyr.save()
                lyr_file = lp.get_layer_file()
                if lyr_file and not lyr.file:
                    fname = os.path.basename(lyr_file.path)
                    lyr.file.save(fname, lyr_file)

                for p in SessionBase.objects.filter(layer=l):
                    p.lyr = lyr
                    p.save()

    def create_new_links(self):

        if not self.dry_run:
            links = DocumentLink.objects.all()
            print(f"clearing {links.count()} existing links")
            links.delete()

        doc_ct = ContentType.objects.get(app_label="georeference", model="document")
        sls = SplitDocumentLink.objects.all()
        print(f"{sls.count()} SplitDocumentLinks to replicate")
        for sl in SplitDocumentLink.objects.all():
            if Document.objects.filter(pk=sl.document.pk).exists():
                if Document.objects.filter(pk=sl.object_id).exists():
                    if self.verbosity >= 2:
                        print(sl)
                    if not self.dry_run:
                        DocumentLink.objects.create(
                            source=Document.objects.get(pk=sl.document.pk),
                            target_type=doc_ct,
                            target_id=sl.object_id,
                            link_type="split",
                        )

        lyr_ct = ContentType.objects.get(app_label="georeference", model="layer")
        gls = GeoreferencedDocumentLink.objects.all()
        print(f"{gls.count()} GeoreferencedDocumentLinks to replicate")
        for sl in gls:
            if Document.objects.filter(pk=sl.document.pk).exists():
                if Layer.objects.filter(pk=sl.object_id).exists():
                    if self.verbosity >= 2:
                        print(sl)
                    if not self.dry_run:
                        DocumentLink.objects.create(
                            source=Document.objects.get(pk=sl.document.pk),
                            target_type=lyr_ct,
                            target_id=sl.object_id,
                            link_type="georeference",
                        )

    def update_volumes(self, city=None):

        if city is not None:
            volumes = Volume.objects.filter(city=city)
        else:
            volumes = Volume.objects.all()

        print(f"{volumes.count()} volumes to update")

        for v in volumes:
            if self.verbosity >= 2:
                print(v)
            if not self.dry_run:
                old_main = [i for i in v.ordered_layers["layers"] if i.startswith("geonode:")]
                old_index = [i for i in v.ordered_layers["index_layers"] if i.startswith("geonode:")]

                v.sorted_layers["main"] = list(set([i.replace("geonode:", "") for i in old_main]))
                v.sorted_layers["key_map"] = list(set([i.replace("geonode:", "") for i in old_index]))
                v.save()

                v.refresh_lookups()