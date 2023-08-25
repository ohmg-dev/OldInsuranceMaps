import os
import json
from django.core import management
from django.core.management.base import BaseCommand, CommandError
from django.contrib.contenttypes.models import ContentType

from ohmg.loc_insurancemaps.models import Volume

class Command(BaseCommand):
    help = 'management command for migration initialization'
    verbose = False

    def add_arguments(self, parser):

        parser.add_argument(
            "source",
            help="directory containing fixtures to load",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            default=False,
            help="Verbose output.",
        )

    def handle(self, *args, **options):

        self.verbose = options["verbose"]
        
        management.call_command("loaddata", os.path.join(options['source'], "all_sites.json"))
        users_file = self.convert_profiles_to_users(options['source'])
        management.call_command("loaddata", users_file)
        management.call_command("loaddata", os.path.join(options['source'], "all_avatars.json"))
        management.call_command("loaddata", os.path.join(options['source'], "all_newsletter.json"))
        management.call_command("loaddata", os.path.join(options['source'], "all_places.json"))
        georeference_data_file = self.convert_content_types(options['source'])
        management.call_command("loaddata", georeference_data_file)
        management.call_command("loaddata", os.path.join(options['source'], "all_volumes.json"))
        management.call_command("loaddata", os.path.join(options['source'], "all_sheets.json"))

        for v in Volume.objects.all():
            v.set_extent()

    def convert_profiles_to_users(self, source_dir):

        with open(os.path.join(source_dir, "all_profiles.json"), "r") as j:
            data = json.load(j)

            users = []
            for profile in data:
                if profile['pk'] == -1:
                    continue
                users.append({
                    'model': 'accounts.User',
                    'pk': profile['pk'],
                    'fields': {
                    'password': profile['fields']['password'],
                    'last_login': profile['fields']['last_login'],
                    'is_superuser': profile['fields']['is_superuser'],
                    'username': profile['fields']['username'],
                    'first_name': profile['fields']['first_name'],
                    'last_name': profile['fields']['last_name'],
                    'email': profile['fields']['email'],
                    'is_staff': profile['fields']['is_staff'],
                    'is_active': profile['fields']['is_active'],
                    'date_joined': profile['fields']['date_joined'],
                    }
                })

        out_path = os.path.join(source_dir, "all_users.json")
        with open(out_path, "w") as out:
            json.dump(users, out, indent=2)

        return out_path

    def convert_content_types(self, source_dir):

        with open(os.path.join(source_dir, "all_georeference_data.json"), "r") as j:
            data = json.load(j)

        doc_ct = ContentType.objects.get(app_label='georeference', model='document').pk
        lyr_ct = ContentType.objects.get(app_label='georeference', model='layer').pk
        
        out_content = []

        for i in data:
            if i["model"] == "georeference.documentlink":
                if i['fields']['link_type'] == "split":
                    i['fields']['target_type'] = doc_ct
                if i['fields']['link_type'] == "georeference":
                    i['fields']['target_type'] = lyr_ct
            out_content.append(i)

        out_path = os.path.join(source_dir, "all_georeference_updates.json")
        with open(out_path, "w") as out:
            json.dump(out_content, out, indent=2)

        return out_path