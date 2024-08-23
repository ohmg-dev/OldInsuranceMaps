
import json
from datetime import datetime

from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Polygon

from ohmg.core.models import (
    MapGroup,
    Map,
    Document,
    Region,
    Layer,
)
from ohmg.core.utils import save_file_to_object
from ohmg.loc_insurancemaps.models import Sheet, Volume
from ohmg.georeference.models import (
    Document as OldDocument,
    LayerV1,
    LayerSet,
    PrepSession,
    GeorefSession,
    SessionLock,
)

ts = datetime.now().strftime("%Y_%m_%d__%H%M")
def print_to_log(msg):
    with open(f"migration_log_{ts}.txt", "a") as f:
        f.write(f"{msg}\n")

class Command(BaseCommand):
    help = 'command to search the Library of Congress API.'

    def add_arguments(self, parser):
        parser.add_argument(
            "--clean",
            action="store_true",
            help="deletes all instances of new models before running the migration operations",
        )
        parser.add_argument(
            "--no-files",
            action="store_true",
            help="don't copy files over during migration (use during local testing)",
        )

    def handle(self, *args, **options):
        """ Migrates all of the existing content into new core models.
        OLD MODEL --> NEW MODEL
        Volumes --> Maps
        Sheets --> Documents (new)*
        Documents (old) --> Regions*
        Layers --> Layers*

        Regions must be created for
            1) every document that was not split, and
            2) every child from a split document.
        Layers will be made from all existing LayerV1s, and linked to the proper Region.
        Documents (new) will be made for all Sheets, however, they will be more similar
        to the Documents (old) that already exist for all Sheets.
        """           

        if options['clean']:
            models_to_clean = [
                SessionLock,
                Layer,
                Region,
                Document,
                # Map, don't delete Maps, as this will delete all LayerSets (bad)
                MapGroup,
            ]
            for m in models_to_clean:
                objs = m.objects.all()
                print(f"deleting {len(objs)} {m}")
                objs.delete()

        for vol in Volume.objects.all():
            print(f"Processing: {vol}")
            map, created = Map.objects.get_or_create(
                title=vol.__str__(),
                identifier=vol.identifier,
                volume_number=vol.volume_no,
                document_page_type="page",
                year=vol.year,
                month=vol.month,
                loaded_by=vol.loaded_by,
                load_date=vol.load_date,
            )
            if not created:
                print("  -- using existing map object")
            map.locales.set(vol.locales.all())

            for sheet in vol.sheets:
                if sheet.doc:
                    # hacky method for pulling out the sheet number from the title
                    page_number = ""
                    try:
                        page_number = sheet.doc.title.split("|")[-1].split("p")[1]
                    except IndexError:
                        print_to_log(f"[ERROR] can't get page number from doc title {sheet.doc} ({sheet.doc.pk})")
                    if page_number == "":
                        page_number = "0"
                    new_doc = Document.objects.create(
                        pk=sheet.doc.pk,
                        map=map,
                        page_number=page_number,
                    )
                    if not options['no_files']:
                        save_file_to_object(new_doc, source_object=sheet.doc)

                    # find the existing session for this document and attach the new doc to it
                    prep_sessions = PrepSession.objects.filter(doc=sheet.doc)
                    if len(prep_sessions) > 1:
                        print_to_log(f"[ERROR] Too many prep sessions for this document: {sheet.doc} ({sheet.doc.pk})")
                    if prep_sessions.exists():
                        prep_sessions[0].doc2 = new_doc
                        prep_sessions[0].save()

                    # if there is only one real document for this sheet, then use it to make
                    # a new Region, but only if that one document is not "unprepared".
                    if len(sheet.real_docs) == 1:
                        if sheet.doc.status != "unprepared":
                            # use a fake boundary if there aren't local files available
                            if options['no_files']:
                                w, h = 10, 10
                            else:
                                w, h = sheet.doc.image_size
                            is_map = True
                            if sheet.doc.vrs and sheet.doc.vrs.category.slug == "non-map-content":
                                is_map = False
                            region = Region.objects.create(
                                boundary = Polygon([[0,0], [0,h], [w,h], [w,0], [0,0]]),
                                document=new_doc,
                                gcp_group=sheet.doc.gcp_group,
                                is_map=is_map,
                            )
                            if not options['no_files']:
                                save_file_to_object(region, source_object=new_doc)

                    # if there are more than one real documents for this sheet, make a new
                    # Region for both of them, because these documents represent split children
                    else:
                        divisions = sheet.doc.preparation_session.data['divisions']
                        if not len(divisions) == len(sheet.real_docs):
                            print_to_log(f"[ERROR] Division mismatch: {len(divisions)} divisions, {len(sheet.real_docs)} real_docs (sheet: {sheet.pk})")
                        for div_no, div in enumerate(divisions, start=1):
                            matching_old_doc = [i for i in sheet.real_docs if int(i.slug.split("_")[-1]) == div_no][0]
                            is_map = True
                            if matching_old_doc.vrs and matching_old_doc.vrs.category.slug == "non-map-content":
                                is_map = False
                            div_poly = Polygon(div)
                            region = Region.objects.create(
                                boundary=div_poly,
                                document=new_doc,
                                division_number=div_no,
                                gcp_group=matching_old_doc.gcp_group,
                                created_by=matching_old_doc.preparation_session.user,
                                is_map=is_map
                            )
                            if not options['no_files']:
                                save_file_to_object(region, source_object=matching_old_doc)
                else:
                    print_to_log(f"[WARNING] this sheet has no document {sheet} ({sheet.pk})")

        # now, separately, iterate all old layers and create new ones from them
        existing_layers = LayerV1.objects.all()
        matched = []
        for old_layer in existing_layers:

            old_doc = old_layer.get_document()
            if not old_doc:
                print_to_log(f"[ERROR] This layer has no doc: {old_layer} ({old_layer.pk})")
                continue
            old_doc_parent = old_doc.parent
            if old_doc_parent:
                # if the original document has a parent, that means it was generated from
                # a split operation. In this case, need to find the Region that corresponds
                # to it
                new_doc = Document.objects.get(pk=old_doc_parent.pk)
                doc_regions = new_doc.regions.all()
                if len(doc_regions) <= 1:
                    print_to_log(f"[ERROR] {len(doc_regions)} regions on {new_doc} ({new_doc.pk}): this should be > 1")
                    continue
                for region in doc_regions:
                    # use the number at the end of the slug to match
                    if region.division_number == int(old_doc.slug.split("_")[-1]):
                        new_layer = Layer.objects.create(
                            pk=old_layer.pk,
                            region=region,
                            layerset=old_layer.vrs,
                        )
                        if not options['no_files']:
                            save_file_to_object(new_layer, source_object=old_layer)
                        matched.append(old_layer.pk)
            else:
                # if not, then this new layer should be attached to the region that was created
                # from the full old_doc
                new_doc = Document.objects.get(pk=old_doc.pk)
                doc_regions = new_doc.regions.all()
                if len(doc_regions) != 1:
                    print_to_log(f"[ERROR] during layer {old_layer} ({old_layer.pk}) creation {len(doc_regions)} regions on {new_doc} ({new_doc.pk}): this should be 1")
                    continue
                new_layer = Layer.objects.create(
                    pk=old_layer.pk,
                    region=doc_regions[0],
                    layerset=old_layer.vrs,
                )
                if not options['no_files']:
                    save_file_to_object(new_layer, source_object=old_layer)
                matched.append(old_layer.pk)


            # find the existing session for this document and attach the new doc to it
            georef_sessions = GeorefSession.objects.filter(lyr=old_layer)
            if len(georef_sessions) == 0:
                print_to_log(f"[ERROR] Why are there no georef sessions for this old layer?? {old_layer.slug} ({old_layer.pk})")
                continue

            for gs in georef_sessions:
                gs.reg2 = new_layer.region
                gs.lyr2 = new_layer
                gs.save()

        if len(existing_layers) != len(matched):
            print_to_log("[WARNING] the following layers were not matched to new regions")
            for missing in [i for i in existing_layers if i.pk not in matched]:
                print_to_log(missing)

        for layerset in LayerSet.objects.all():

            if layerset.category.slug == "non-map-content":
                continue

            # attach new maps corresponding to old volumes. This doubles as a lookup
            # of old against new
            map = Map.objects.get(pk=layerset.volume.pk)
            layerset.map = map
            layerset.save()

            ## make sure the old list of layers on this layerset is identical
            ## to the new list. This also (basically) ensures that the same pks
            ## have been used for all the new layers.
            annotation_list_old = sorted([i.pk for i in layerset.annotations])
            layer_list_new = sorted([i.pk for i in layerset.layers.all()])
            if annotation_list_old != layer_list_new:
                print_to_log(f"[WARNING] LayerSet {layerset} may not have the correct layers")
                print_to_log(f"old annotations: {len(annotation_list_old)} new layers: {len(layer_list_new)}")

        counts = {
            'volumes': Volume.objects.all().count(),
            'maps': Map.objects.all().count(),
            'sheets': Sheet.objects.all().count(),
            'documents_old': OldDocument.objects.all().count(),
            'documents_new': Document.objects.all().count(),
            'regions': Region.objects.all().count(),
            'layers_old': LayerV1.objects.all().count(),
            'layers_new': Layer.objects.all().count(),
        }

        print(json.dumps(counts, indent=1))

        print(f"Volumes == Maps: {counts['volumes']==counts['maps']}")
        print(f"Sheets == New Documents: {counts['sheets']==counts['documents_new']}")
        print(f"Old Layers == New Layers: {counts['layers_old']==counts['layers_new']}")

        print("final checks on new relations...")
        for i in Document.objects.all():
            if not i.map:
                print(f"{i} has no map but should have one")
        for i in Region.objects.all():
            if not i.document:
                print(f"{i} has no document but should have one")
        for i in Layer.objects.all():
            if not i.region:
                print(f"{i} has no region but should have one")

    def make_map_groups(self):
        """ Collect all of the existing maps in the database and create MapGroups, or
        add to existing MapGroups, as needed."""

        locales_with_maps = list(set(Map.objects.all().values_list("locales", flat=True)))
        print(locales_with_maps)
