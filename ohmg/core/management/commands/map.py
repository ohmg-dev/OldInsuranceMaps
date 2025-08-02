from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from ohmg.core.importers.base import get_importer
from ohmg.core.models import Map
from ohmg.georeference.models import PrepSession, GeorefSession


class Command(BaseCommand):
    help = "management command to handle map object operations"

    def add_arguments(self, parser):
        (
            parser.add_argument(
                "operation",
                choices=[
                    "add",
                    "remove",
                    "list-importers",
                    "add-document",
                    "create-documents",
                    "create-lookups",
                    "refresh-lookups",
                ],
                help="the operation to perform",
            ),
        )
        (
            parser.add_argument(
                "--pk",
                help="id of map",
            ),
        )
        (
            parser.add_argument(
                "--bulk-file",
                help="path to file for bulk import",
            ),
        )
        (
            parser.add_argument(
                "--dry-run",
                action="store_true",
                default=False,
                help="perform a dry-run of the operation",
            ),
        )
        (
            parser.add_argument(
                "--get-files",
                action="store_true",
                default=False,
                help="Will download all files to documents, during the create-documents operation",
            ),
        )
        (
            parser.add_argument(
                "--overwrite",
                action="store_true",
                default=False,
                help="overwrite existing content with new input",
            ),
        )
        parser.add_argument(
            "--background",
            action="store_true",
            help="run the operation in the background with celery",
        )
        parser.add_argument("--username", help="username to use for load operation")
        parser.add_argument(
            "--skip-existing",
            action="store_true",
            default=False,
            help="During Map lookup refresh: skip any Maps that don't have null lookups. During bulk map load: Don't throw an error if one of the maps already exists, just move on to the next one.",
        )
        parser.add_argument(
            "--force",
            help="force operation (no confirmation dialog)",
            action="store_true",
        )
        parser.add_argument(
            "--verbose",
            help="print verbose output during process",
            action="store_true",
            default=False,
        )
        parser.add_argument(
            "-c",
            "--config",
            default="default",
            help="id of importer class to use, from list of options in settings.IMPORTERS['map']",
        )
        parser.add_argument(
            "--opts", nargs="*", help="arguments to pass to selected importer class operation"
        )

    def handle(self, *args, **options):
        operation = options["operation"]

        if operation == "add":
            if options["config"] not in settings.OHMG_IMPORTERS["map"]:
                raise NotImplementedError("no entry in settings.OHMG_IMPORTERS for this importer")

            importer = get_importer(
                options["config"],
                dry_run=options["dry_run"],
                overwrite=options["overwrite"],
                verbose=options["verbose"],
                skip_existing=options["skip_existing"],
            )

            importer_kwargs = {}
            if options["opts"]:
                for opt in options["opts"]:
                    if "=" not in opt:
                        raise ValueError(f"{opt} is a malformed opt. Format must be key=value.")

                    key, value = opt.split("=")
                    importer_kwargs[key] = value

                importer.run_import(**importer_kwargs)

            elif options["bulk_file"]:
                importer.run_bulk_import(options["bulk_file"])

        if operation == "remove":
            try:
                map = Map.objects.get(pk=options["pk"])
            except Map.DoesNotExist:
                print("this map does not exist in the database")
                exit()

            documents = list(map.documents.all())
            regions = []
            for d in documents:
                regions += list(d.regions.all())
            layers = [i.layer for i in regions if hasattr(i, "layer")]
            gcpgroups = [i.region.gcpgroup for i in layers if hasattr(i.region, "gcpgroup")]
            gcps = []
            for gcpgroup in gcpgroups:
                gcps += list(gcpgroup.gcps.all())

            prep_sessions = list(PrepSession.objects.filter(doc2__in=documents))
            georef_sessions = list(GeorefSession.objects.filter(reg2__in=regions))

            print(map)
            print(f"documents {len(documents)}")
            print(f"regions {len(regions)}")
            print(f"layers {len(layers)}")
            print(f"gcp groups {len(gcpgroups)}")
            print(f"gcps {len(gcps)}")
            print(f"prep sessions {len(prep_sessions)}")
            print(f"georef sessions {len(georef_sessions)}")

            prompt = "Delete all of these objects? y/N "
            if options["force"] or input(prompt).lower().startswith("y"):
                for i in (
                    prep_sessions
                    + georef_sessions
                    + gcps
                    + gcpgroups
                    + layers
                    + regions
                    + documents
                    + [map]
                ):
                    print(i)
                    i.delete()

            print("objects deleted.")
            print("done")

        if operation == "create-documents":
            if options["username"]:
                username = options["username"]
            else:
                username = "admin"
            user = get_user_model().objects.get(username=username)

            try:
                map = Map.objects.get(pk=options["pk"])
                map.loaded_by = user
                map.save()
            except Map.DoesNotExist:
                print("this map does not exist in the database")
                exit()
            map.create_documents()

        if operation == "list-importers":
            for name in settings.OHMG_IMPORTERS["map"].keys():
                print(f"id: {name}")
                importer = get_importer(name)
                print(importer.__doc__)

        if operation == "refresh-lookups":
            start = datetime.now()
            if options["pk"]:
                maps = [Map.objects.get(pk=options["pk"])]
            elif options["skip_existing"]:
                maps = Map.objects.all().filter(item_lookup__isnull=True).order_by("title")
            else:
                maps = Map.objects.all().order_by("title")

            for map in maps:
                print(map)
                map.update_item_lookup()

            print(f"elapsed_time: {datetime.now() - start}")
