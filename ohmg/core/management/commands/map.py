import csv
from datetime import datetime
import importlib

from django.conf import settings
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from ohmg.core.importers.base import get_importer
from ohmg.loc_insurancemaps.models import Volume
from ohmg.places.models import Place
from ohmg.places.management.utils import reset_volume_counts
from ohmg.georeference.models import ItemBase, LayerV1, DocumentLink

class Command(BaseCommand):
    help = 'management command to handle map object operations'

    def add_arguments(self, parser):
        parser.add_argument(
            "operation",
            choices=[
                "add",
                "remove",
                "list-importers",
                "add-document",

                "refresh-lookups",
                "make-sheets",
                "generate-mosaic-cog",
                "generate-mosaic-json",
                "generate-thumbnails",
                "set-extent",
                "warp-layers",
            ],
            help="the operation to perform",
        ),
        parser.add_argument(
            "--pk",
            help="id of map",
        ),
        parser.add_argument(
            "--csv-file",
            help="path to file for bulk import",
        ),
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="perform a dry-run of the operation",
        ),
        parser.add_argument(
            "--overwrite",
            action="store_true",
            default=False,
            help="overwrite existing content with new input",
        ),
        parser.add_argument(
            "--load-documents",
            action="store_true",
            help="boolean to indicate whether documents should be made for the sheets",
        ),
        parser.add_argument(
            "--background",
            action="store_true",
            help="run the operation in the background with celery"
        )
        parser.add_argument(
            "--username",
            help="username to use for load operation"
        )
        parser.add_argument(
            "--force",
            help="force operation (no confirmation dialog)",
            action="store_true",
        )
        parser.add_argument(
            "--importer",
            default="single-file",
            help="id of importer class to use, from list of options in settings.IMPORTERS['map']"
        )
        parser.add_argument(
            "--opts",
            nargs="*",
            # help="id of importer class to use, from list of options in settings.IMPORTERS['map']"
        )

    def handle(self, *args, **options):

        operation = options['operation']

        if options['username']:
            username = options['username']
        else:
            username = "admin"
        user = get_user_model().objects.get(username=username)

        if operation == "add":
            if options['importer'] not in settings.OHMG_IMPORTERS['map']:
                raise NotImplementedError("no entry in settings.OHMG_IMPORTERS for this importer")

            importer = get_importer(options['importer'], dry_run=options['dry_run'], overwrite=options['overwrite'])

            importer_kwargs = {}
            if options['opts']:
                for opt in options['opts']:
                    if "=" not in opt:
                        raise ValueError(f"{opt} is a malformed opt. Format must be key=value.")

                    key, value = opt.split("=")
                    importer_kwargs[key] = value
    
                importer.run_import(**importer_kwargs)

            elif options['csv-file']:
                importer.run_bulk_import(options['csv-file'])

        if operation == "remove":
            try:
                vol = Volume.objects.get(pk=options["pk"])
            except Volume.DoesNotExist:
                print("this map does not exist in the database")
                exit()

            sheets = list(vol.sheets)
            documents = []
            layers = []
            gcp_groups = []
            all_gcps = []
            sessions = []
            doc_links = []

            for s in sheets:
                if s.doc:
                    documents.append(s.doc)
                    sessions += s.doc.get_sessions()
                    documents += s.doc.children
                    doc_links += list(DocumentLink.objects.filter(source=s.doc))
                    layer = s.doc.get_layer()
                    if layer:
                        layers.append(layer)
                        gcp_group = s.doc.gcp_group
                        gcp_groups.append(gcp_group)
                        all_gcps += list(gcp_group.gcps)


            print(vol)
            print(f"sheets {len(sheets)}")
            print(f"documents {len(documents)}")
            print(f"layers {len(layers)}")
            print(f"gcp groups {len(gcp_groups)}")
            print(f"gcps {len(all_gcps)}")
            print(f"sessions {len(sessions)}")
            print(f"document links: {len(doc_links)}")

            prompt = "Delete all of these objects? y/N "
            if options["force"] or input(prompt).lower().startswith("y"):
                for i in sessions + all_gcps + gcp_groups + layers + doc_links + documents + sheets + [vol]:
                    print(i)
                    i.delete()

            print("onjects deleted. resetting map counts...")
            reset_volume_counts()
            print("done")

        if operation == "list-importers":
            for name in settings.OHMG_IMPORTERS['map'].keys():
                print(f"id: {name}")
                importer = get_importer(name)
                print(importer.__doc__)
