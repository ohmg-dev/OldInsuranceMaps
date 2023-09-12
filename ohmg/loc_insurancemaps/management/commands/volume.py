from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model

from ohmg.content.models import Item
from ohmg.loc_insurancemaps.tasks import (
    generate_mosaic_cog_task,
    generate_mosaic_json_task,
)
from ohmg.loc_insurancemaps.models import Volume
from ohmg.places.models import Place as NewPlace
from ohmg.georeference.models.resources import ItemBase, Layer

class Command(BaseCommand):
    help = 'command to search the Library of Congress API.'

    def add_arguments(self, parser):
        parser.add_argument(
            "operation",
            choices=[
                "import",
                "refresh-lookups-old",
                "refresh-lookups",
                "make-sheets",
                "generate-mosaic-cog",
                "generate-mosaic-json",
                "generate-non-geo-mosaic",
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
            "--all",
            help="apply to all volumes",
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

        i = options['identifier']
        if options['operation'] == "refresh-lookups":
            if i is not None:
                vols = Volume.objects.filter(pk=i)
            else:
                vols = Volume.objects.all()
            for v in vols:
                v.refresh_lookups()
            print(f"refreshed lookups on {len(vols)} volumes")

        if options['operation'] == "refresh-lookups-old":
            if i is not None:
                vols = Volume.objects.filter(pk=i)
            else:
                vols = Volume.objects.all()
            for v in vols:
                v.populate_lookups()
            print(f"refreshed lookups on {len(vols)} volumes")

        if options['operation'] == "import":

            locale_slug = options['locale']
            locale = None
            if locale_slug is not None:
                try:
                    print(f'locale slug: {locale_slug}')
                    locale = NewPlace.objects.get(slug=locale_slug)
                    print(f'using locale: {locale}')
                except NewPlace.DoesNotExist:
                    confirm = input('no locale matching this slug, locale will be None. continue? y/N ')
                    if not confirm.lower().startswith("y"):
                        exit()

            vol = Volume().import_volume(i, locale=locale)
            print(vol)

        if options['operation'] == "make-sheets":
            vol = Volume.objects.get(pk=i)
            vol.make_sheets()
            if options['load_documents']:
                vol.loaded_by = user
                vol.load_date = datetime.now()
                vol.save(update_fields=["loaded_by", "load_date"])
                vol.load_sheet_docs(force_reload=True)

        if options['operation'] == "generate-mosaic-cog":
            if i is not None:
                if options['background']:
                    generate_mosaic_cog_task.delay(i)
                else:
                    item = Item(i)
                    item.generate_mosaic_cog()

        if options['operation'] == "generate-non-geo-mosaic":
            if i is not None:
                if options['background']:
                    print('not implemented')
                    return
                    #generate_mosaic_cog_task.delay(i)
                else:
                    item = Item(i)
                    item.export_mosaic_jpg(f"{i}.jpg")

        if options['operation'] == "generate-mosaic-json":
            if i is not None:
                if options['background']:
                    generate_mosaic_json_task.delay(i, trim_all=options['trim_all'])
                else:
                    item = Item(i)
                    item.generate_mosaic_json(trim_all=options['trim_all'])

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
                for l in v.layer_lookup.keys():
                    s = ItemBase.objects.filter(slug=l)
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
                for l in v.layer_lookup.keys():
                    print(f'  {l}')
                    ss = Layer.objects.filter(slug=l)
                    for s in ss:
                        latest_sesh = list(s.get_document().georeference_sessions)[-1]
                        print(f"  running session {latest_sesh.pk}")
                        latest_sesh.run()
                        print("    done")
