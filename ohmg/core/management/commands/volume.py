import csv
from datetime import datetime

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from ohmg.core.importers.loc_sanborn import import_volume
from ohmg.loc_insurancemaps.models import Volume
from ohmg.places.models import Place
from ohmg.places.management.utils import reset_volume_counts
from ohmg.georeference.models import ItemBase, LayerV1, DocumentLink

class Command(BaseCommand):
    help = 'command to search the Library of Congress API.'

    def add_arguments(self, parser):
        parser.add_argument(
            "operation",
            choices=[
                "import",
                "remove",
                "refresh-lookups-old",
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
            "-i", "--identifier",
            help="the identifier of the LoC resource to add",
        ),
        parser.add_argument(
            "-f", "--csv-file",
            help="path to file for bulk import",
        ),
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="perform a dry-run of the operation",
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
            "--trim-all",
            action="store_true",
            default=False,
            help="re-trim all layers during mosaic JSON creation"
        )
        parser.add_argument(
            "--username",
            help="username to use for load operation"
        )
        parser.add_argument(
            "--locale",
            help="slug for the Place to attach to this volume"
        )
        parser.add_argument(
            "--sponsor",
            help="username of sponsor for this volume"
        )
        parser.add_argument(
            "--access",
            default="any",
            help="username of sponsor for this volume"
        )
        parser.add_argument(
            "--all",
            help="apply to all volumes",
            action="store_true",
        )
        parser.add_argument(
            "--no-cache",
            help="don't use cached request response",
            action="store_true",
        )
        parser.add_argument(
            "-e", "--exclude",
            nargs="*",
            help="identifiers of volumes to exclude, used in conjunction with --all."
        )

    def handle(self, *args, **options):

        if options['username']:
            username = options['username']
        else:
            username = "admin"
        user = get_user_model().objects.get(username=username)

        sponsor = None
        if options['sponsor']:
            sponsor = get_user_model().objects.get(username=options['sponsor'])

        i = options['identifier']
        if options['operation'] == "refresh-lookups":
            if i is not None:
                vols = Volume.objects.filter(pk=i)
            else:
                vols = Volume.objects.all()
            for v in vols:
                v.refresh_lookups()
            print(f"refreshed lookups on {len(vols)} volumes")

        if options['operation'] == "import":

            def get_locale(locale_slug):
                try:
                    print(f'locale slug: {locale_slug}')
                    locale = Place.objects.get(slug=locale_slug)
                    print(f'using locale: {locale}')
                except Place.DoesNotExist:
                    locale = None
                return locale

            to_load = []

            if i:
                locale = get_locale(options['locale'])
                if locale is None:
                    confirm = input('no locale matching this slug, locale will be None. continue? y/N ')
                    if not confirm.lower().startswith("y"):
                        exit()
                to_load.append((i, locale))

            elif options['csv_file']:

                with open(options['csv_file'], "r") as o:
                    reader = csv.DictReader(o)
                    for row in reader:
                        if "identifier" not in row or "locale" not in row:
                            print("missing info in row")
                            print(row)
                            continue
                        locale = get_locale(row['locale'])
                        if locale is None:
                            print(f"can't find locale {row['locale']}, skipping.")
                            continue
                        to_load.append((row["identifier"], locale))

            for identifier, locale in to_load:
                vol = import_volume(
                    identifier,
                    locale=locale,
                    dry_run=options['dry_run'],
                    no_cache=options['no_cache'],
                )
                if vol:
                    vol.access = options['access']
                    vol.sponsor = sponsor
                    vol.save()
                print(vol)

        if options['operation'] == "remove":
            vol = Volume.objects.get(pk=i)

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

            confirm = input("Delete all of these objects? y/N ")
            if confirm.lower().startswith("y"):
                for i in sessions + all_gcps + gcp_groups + layers + doc_links + documents + sheets + [vol]:
                    print(i)
                    i.delete()

            reset_volume_counts()

        if options['operation'] == "make-sheets":
            vol = Volume.objects.get(pk=i)
            vol.make_sheets()
            if options['load_documents']:
                vol.loaded_by = user
                vol.load_date = datetime.now()
                vol.save(update_fields=["loaded_by", "load_date"])
                vol.load_sheet_docs(force_reload=True)

        if options['operation'] == "set-extent":
            if i is not None:
                vol = Volume.objects.get(identifier=i)
                vol.set_extent()

        if options['operation'] == 'generate-thumbnails':
            volumes = []
            if options['identifier']:
                volumes += [Volume.objects.get(pk=options['identifier'])]
            elif options['all']:
                volumes += Volume.objects.all()

            for v in volumes:
                print(v)
                for i in v.document_lookup.keys():
                    print(i)
                    d = ItemBase.objects.get(pk=i)
                    d.set_thumbnail()
                for i in v.layer_lookup.keys():
                    s = ItemBase.objects.filter(slug=i)
                    for ss in s:
                        print(ss)
                        ss.set_thumbnail()
                print("refreshing volume lookup.")
                v.refresh_lookups()

        if options['operation'] == 'warp-layers':
            volumes = []
            if options['identifier']:
                volumes += [Volume.objects.get(pk=options['identifier'])]
            elif options['all']:
                volumes += Volume.objects.all()
            for v in volumes:
                if v.identifier in options['exclude']:
                    print(f"skipping excluded: {v.identifier}")
                    continue
                print(f'{v.identifier} - {v.__str__()}')
                for i in v.layer_lookup.keys():
                    print(f'  {i}')
                    ss = LayerV1.objects.filter(slug=i)
                    for s in ss:
                        latest_sesh = list(s.get_document().georeference_sessions)[-1]
                        print(f"  running session {latest_sesh.pk}")
                        latest_sesh.run()
                        print("    done")
