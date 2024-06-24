
import json
import time

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Polygon

from ohmg.core.models import (
    MapGroup,
    Map,
    Document,
    Region,
)
from ohmg.core.utils import make_cacheable_request

from ohmg.loc_insurancemaps.models import Sheet, Volume, find_volume
from ohmg.georeference.models import Document as OldDocument

class Command(BaseCommand):
    help = 'command to search the Library of Congress API.'

    def add_arguments(self, parser):
        parser.add_argument(
            "--clean",
            action="store_true",
            help="deletes all instances of new models before running the migration operations",
        )

    def handle(self, *args, **options):
        """ Migrates all of the existing content into new core models.
        OLD MODEL --> NEW MODEL
        Volumes --> Maps
        Sheets --> Documents (new)*
        Documents (old) --> Regions*
        Layers --> Layers*

        Regions must be created for
            1) every document that was not split, or
            2) every child from a split document.
        Layers will be made from all existing LayerV1s, and linked to the proper Region.
        Documents (new) will be made for all Sheets, however, they will be more similar
        to the Documents (old) that already exist for all Sheets.
        """

        # counts = {
        #     'vols': 0,
        #     'sheets': 0,
        #     'documents'
        # }

        if options['clean']:
            models = [MapGroup, Map, Document, Region]
            for m in models:
                objs = m.objects.all()
                print(f"deleting {len(objs)} {m}")
                objs.delete()

        for vol in Volume.objects.all():

            map = Map.objects.create(
                title=vol.__str__(),
                identifier=vol.identifier,
                volume_number=vol.volume_no,
                document_page_type="page",
            )
            map.locales.set(vol.locales.all())

            for sheet in vol.sheets:
                if sheet.doc:
                    # hacky method for pulling out the sheet number from the title
                    page_number = ""
                    try:
                        page_number = sheet.doc.title.split("|")[-1].split("p")[1]
                    except IndexError as e:
                        print(e)
                        pass
                    new_doc = Document.objects.create(
                        pk=sheet.doc.pk,
                        map=map,
                        page_number=page_number,
                    )
                    print(new_doc, "(document)")

                    if len(sheet.real_docs) == 1:
                        w, h = sheet.doc.image_size
                        region = Region.objects.create(
                            boundary = Polygon([[0,0], [0,h], [w,h], [w,0], [0,0]]),
                            document=new_doc
                        )
                        print(region, "(region)")
                    else:
                        divisions = sheet.doc.preparation_session.data['divisions']
                        assert len(divisions) == len(sheet.real_docs)
                        for n, div in enumerate(divisions):
                            # turn the division into a polygon
                            div_poly = Polygon(div)
                            # make a Polygon from the bbox of this division.
                            div_poly_extent = Polygon().from_bbox(div_poly.extent)
                            # get the document that should have been made from this division
                            corresponding_doc = sheet.real_docs[n]
                            # create a Polygon from the dimensions of this document's file
                            w, h = corresponding_doc.image_size
                            doc_poly = Polygon([[0,0], [0,h], [w,h], [w,0], [0,0]])

                            # the division bbox area and doc file area should be extremely
                            # similar in size, the difference will be problematic down the road
                            # however, initial inspection shows that the matching documents are
                            # properly linked to the correct divisions.
                            # # keep in mind these areas are in pixels...
                            # print(div_poly_extent.area, doc_poly.area)
                            region = Region.objects.create(
                                boundary = Polygon([[0,0], [0,h], [w,h], [w,0], [0,0]]),
                                document=new_doc,
                                division_number = n+1,
                            )
                            print(region, "(region)")

    def make_map_groups(self):
        """ Collect all of the existing maps in the database and create MapGroups, or
        add to existing MapGroups, as needed."""

        locales_with_maps = list(set(Map.objects.all().values_list("locales", flat=True)))
        print(locales_with_maps)