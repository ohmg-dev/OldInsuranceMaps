import os
import csv

from django.conf import settings
from django.core import management
from django.core.management.base import BaseCommand, CommandError

from lc_insurancemaps.api import APIConnection
from lc_insurancemaps.utils import parsers, enumerations
from lc_insurancemaps.utils.importer import Importer
from lc_insurancemaps.models import Volume

class Command(BaseCommand):
    help = 'command to search the Library of Congress API.'

    def add_arguments(self, parser):
        parser.add_argument(
            "operation",
            choices=["import", "summarize", "clean", "initialize-volume"],
            help="the identifier of the LoC resource to add",
        )
        parser.add_argument(
            "-i",
            "--identifier",
            help="the identifier of the LoC resource to add",
        )
        parser.add_argument(
            "-l",
            "--location",
            nargs="+",
            default=[],
            help="one or more place names to add to the search query",
        )
        parser.add_argument(
            "--state", help="specifically refine by state",
        )
        parser.add_argument(
            "--city", help="specifically refine by city",
        )
        parser.add_argument(
            "--county", help="specifically refine by county",
        )
        parser.add_argument(
            "--year",
            help="year of volume retrieved",
        )
        parser.add_argument(
            "--no-cache",
            action="store_true",
            help="don't use a cached version of this query",
        )
        parser.add_argument(
            "--clean",
            action="store_true",
            help="clears all MapCollectionItem objects before running",
        )
        parser.add_argument(
            "--import-sheets",
            action="store_true",
            help="also acquires all sheets for the added items",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="performs the search and retrieval but creates no ORM objects",
        )
        parser.add_argument(
            "--write-files",
            action="store_true",
            help="write summary files",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            default=False,
            help="write messages during process",
        )

    def handle(self, *args, **options):

        if options['operation'] == "clean" or options['clean']:
            management.call_command("clear_insurancemaps", "--all")

        if options['operation'] == "import":

            i = Importer(
                dry_run=options["dry_run"],
                verbose=options["verbose"],
            )

            i.import_volumes(
                state=options["state"],
                city=options["city"],
                year=options["year"],
                import_sheets=options["import_sheets"],
            )
        
        if options['operation'] == "initialize-volume":
            i = Importer(
                dry_run=options["dry_run"],
                verbose=options["verbose"],
            )
            i.initialize_volume(options["identifier"])

        if options['operation'] == "summarize":

            lc = APIConnection(verbose=options['verbose'])

            # combine all location arguments
            locations = options['location']
            if options['state']:
                statel = options['state'].lower()
                if statel in enumerations.STATE_NAMES:
                    locations.append(statel)
                else:
                    print("invalid state: " + options["state"])
            if options['city']:
                locations.append(options['city'])
            if options['county']:
                locations.append(options['county'])

            lc.get_items(
                locations=locations,
                no_cache=options['no_cache'],
                year=options['date'],
            )

            volumes = {}
            for item in lc.results:
                loc_info = parsers.parse_location_info(item)
                date_info = parsers.parse_date_info(item)

                info = {
                    "id": item['id'],
                    "city": loc_info['city'],
                    "state": loc_info['state'],
                    "county": loc_info['county'],
                    "year": date_info['year'],
                    "month": date_info['month'],
                    "sheets": item['resources'][0]['files'],
                }

                if options['state'] or options['city'] or options['county']:
                    if options['state']:
                        if options['state'].lower() == loc_info['state'].lower():
                            volumes[item['id']] = info
                    if options['city']:
                        if options['city'].lower() == loc_info['city'].lower():
                            volumes[item['id']] = info
                    if options['county']:
                        if options['county'].lower() == loc_info['county'].lower():
                            volumes[item['id']] = info
                else:
                    volumes[item['id']] = info

            summary_data = {}
            sheet_total = 0
            for k, i in volumes.items():
                sheet_total += i['sheets']
                if i['city'] in summary_data:
                    summary_data[i['city']]['sheets'] += i['sheets']
                    summary_data[i['city']]['volumes'] += 1
                else:
                    summary_data[i['city']] = {
                        'sheets': i['sheets'],
                        'volumes': 1
                    }

            if options['write_files']:
                fileid = ''
                if options['state']:
                    fileid += options['state'] + "_"
                if options['county']:
                    fileid += options['county'] + "_"
                if options['city']:
                    fileid += options['city'] + "_"
                if options['date']:
                    fileid += options['date'].replace("/", "-")
                fileid = fileid.rstrip("_")
                try:
                    outname1 = f"{fileid}--aggregate.csv"
                    with open(os.path.join(settings.CACHE_DIR, outname1), "w") as o:
                        writer = csv.writer(o)
                        writer.writerow(("city", "volumes", "sheets"))
                        for k, v in summary_data.items():
                            writer.writerow((k, v['volumes'], v['sheets']))
                    outname2 = f"{fileid}--full.csv"
                    with open(os.path.join(settings.CACHE_DIR, outname2), "w") as o:
                        writer = csv.writer(o)
                        headers = list(volumes.values())[0].keys()
                        writer.writerow(headers)
                        for id, i in volumes.items():
                            writer.writerow(i.values())
                except Exception as e:
                    print(e)
                    pass

            print(summary_data)
            for k, v in volumes.items():
                print(f"{v['city']}, {v['state']}, {v['county']}, {v['year']} - {v['sheets']} sheets")
            print(f"city count: {len(summary_data)}")
            print(f"volume count: {len(volumes)}")
            print(f"sheet count: {sheet_total}")
