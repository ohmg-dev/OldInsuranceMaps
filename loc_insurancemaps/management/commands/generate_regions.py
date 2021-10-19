import os
import csv
import json

from django.conf import settings
from django.contrib.gis.gdal import DataSource
from django.core import management
from django.core.management.base import BaseCommand, CommandError

from geonode.base.models import Region

from loc_insurancemaps.api import APIConnection
from loc_insurancemaps.utils import parsers, enumerations
from loc_insurancemaps.utils.importer import Importer
from loc_insurancemaps.models import Volume

class Command(BaseCommand):
    help = 'command to search the Library of Congress API.'

    def add_arguments(self, parser):
        parser.add_argument(
            "state", help="generate regions for this state",
        )
        parser.add_argument(
            "--clean",
            action="store_true",
            help="delete all existing Regions before generating new ones",
        )

    def handle(self, *args, **options):

        if options["clean"]:
            Region.objects.all().delete()

        st_code = options["state"].upper()

        appdir = os.path.dirname(os.path.dirname((os.path.dirname(__file__))))
        fixtures_dir = os.path.join(appdir, 'fixtures')
        shp_dir = os.path.join(fixtures_dir, 'data')

        shp_state = os.path.join(shp_dir, "cb_2020_us_state_500k", "cb_2020_us_state_500k.shp")
        shp_county = os.path.join(shp_dir, "cb_2020_us_county_500k", "cb_2020_us_county_500k.shp")
        shp_city = os.path.join(shp_dir, "cb_2020_us_place_500k", "cb_2020_us_place_500k_updated.shp")

        lyr_state = DataSource(shp_state)[0]
        lyr_county = DataSource(shp_county)[0]
        lyr_city = DataSource(shp_city)[0]

        state_feats = {}
        
        for feat in lyr_state:
            state_fp = feat.get("STATEFP")
            code = feat.get("STUSPS")
            if code != st_code:
                continue
            state_feats[code] = feat

        pk = int(state_fp) * 10000
        for code in sorted(state_feats.keys()):
            feat = state_feats[code]
            ext = feat.geom.extent

            reg = Region.objects.get_or_create(
                pk=pk,
                code=feat.get("STUSPS"),
                name=feat.get("NAME"),
                bbox_x0=ext[0],
                bbox_x1=ext[2],
                bbox_y0=ext[1],
                bbox_y1=ext[3],
            )
            pk += 1

        for feat in lyr_city:

            st = feat.get("STUSPS")
            if st != st_code:
                continue
            state = Region.objects.get(code=st)
            name = feat.get("NAME")
            code = feat.get("PLACENS")

            x0, y0, x1, y1 = feat.geom.extent

            reg = Region.objects.get_or_create(
                pk=pk,
                code=code,
                name=name,
                parent=state,
                bbox_x0=x0,
                bbox_x1=y0,
                bbox_y0=x1,
                bbox_y1=y1,
            )
            pk += 1

        outpath = os.path.join(fixtures_dir, f"{st_code.lower()}-regions.json")

        management.call_command(
            "dumpdata",
            "base.Region",
            output=outpath,
            indent=1,
        )

        # with open(outpath, "w") as outfile:
        #     json.dump(output, outfile, indent=1)

        # print(f"fixtures saved to {outpath}")
