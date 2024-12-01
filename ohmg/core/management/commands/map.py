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
                "--csv-file",
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
            help="Used during Map lookup refresh; skip any Maps that don't have null lookups.",
        )
        parser.add_argument(
            "--force",
            help="force operation (no confirmation dialog)",
            action="store_true",
        )
        parser.add_argument(
            "--importer",
            default="single-file",
            help="id of importer class to use, from list of options in settings.IMPORTERS['map']",
        )
        parser.add_argument(
            "--opts",
            nargs="*",
            # help="id of importer class to use, from list of options in settings.IMPORTERS['map']"
        )

    def handle(self, *args, **options):
        operation = options["operation"]

        if options["username"]:
            username = options["username"]
        else:
            username = "admin"
        user = get_user_model().objects.get(username=username)

        if operation == "add":
            if options["importer"] not in settings.OHMG_IMPORTERS["map"]:
                raise NotImplementedError("no entry in settings.OHMG_IMPORTERS for this importer")

            importer = get_importer(
                options["importer"],
                dry_run=options["dry_run"],
                overwrite=options["overwrite"],
            )

            importer_kwargs = {}
            if options["opts"]:
                for opt in options["opts"]:
                    if "=" not in opt:
                        raise ValueError(f"{opt} is a malformed opt. Format must be key=value.")

                    key, value = opt.split("=")
                    importer_kwargs[key] = value

                importer.run_import(**importer_kwargs)

            elif options["csv_file"]:
                importer.run_bulk_import(options["csv_file"])

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
            layers = [i.layer for i in regions if i.layer]
            gcp_groups = [i.region.gcp_group for i in layers if i.region.gcp_group]
            gcps = []
            for gcp_group in gcp_groups:
                gcps += list(gcp_group.gcps.all())

            prep_sessions = list(PrepSession.objects.filter(doc2__in=documents))
            georef_sessions = list(GeorefSession.objects.filter(reg2__in=regions))

            print(map)
            print(f"documents {len(documents)}")
            print(f"regions {len(regions)}")
            print(f"layers {len(layers)}")
            print(f"gcp groups {len(gcp_groups)}")
            print(f"gcps {len(gcps)}")
            print(f"prep sessions {len(prep_sessions)}")
            print(f"georef sessions {len(georef_sessions)}")

            prompt = "Delete all of these objects? y/N "
            if options["force"] or input(prompt).lower().startswith("y"):
                for i in (
                    prep_sessions
                    + georef_sessions
                    + gcps
                    + gcp_groups
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
            try:
                map = Map.objects.get(pk=options["pk"])
                map.loaded_by = user
                map.save()
            except Map.DoesNotExist:
                print("this map does not exist in the database")
                exit()
            map.create_documents(get_files=options["get_files"])

        if operation == "list-importers":
            for name in settings.OHMG_IMPORTERS["map"].keys():
                print(f"id: {name}")
                importer = get_importer(name)
                print(importer.__doc__)

        if operation == "refresh-lookups":
            if options["pk"]:
                maps = [Map.objects.get(pk=options["pk"])]
            elif options["skip_existing"]:
                maps = Map.objects.all().filter(item_lookup__isnull=True)
            else:
                maps = Map.objects.all()

            for map in maps:
                print(map)
                map.update_item_lookup()
