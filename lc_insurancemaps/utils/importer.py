from lc_insurancemaps.models import Volume, Sheet
from lc_insurancemaps.api import APIConnection
from .parsers import parse_fileset, parse_item_identifier, parse_location_info


class Importer(object):

    def __init__(self, verbose=False, dry_run=False, delay=5):
        
        self.verbose = verbose
        self.dry_run = dry_run
        self.delay = delay
    
    def import_volumes(self, state=None, city=None, year=None, import_sheets=False):

        lc = APIConnection(
            delay=self.delay,
            verbose=self.verbose,
        )

        items = lc.get_items(
            locations=[i for i in [state, city] if not i is None],
            year=year,
        )

        if self.verbose:
            print(f"{len(items)} items retrieved")

        volumes = []
        for item in items:
            identifier = parse_item_identifier(item)
            location = parse_location_info(item)
            if location["state"] != state:
                continue
            
            if not self.dry_run:
                vol = Volume().create_from_lc_json(item, location_info=location)
                volumes.append(vol)

            if import_sheets is True and not self.dry_run:
                self.import_sheets(identifier)
        
        return volumes
    
    def import_sheets(self, volume_id):

        vol = Volume.objects.get(identifier=volume_id)
        if vol.lc_resources is None:
            lc = APIConnection(
                delay=self.delay,
                verbose=self.verbose,
            )
            data = lc.get_item(volume_id)
            vol.lc_resources = data['resources']
            vol.save()

        sheets = []
        for fileset in vol.lc_resources[0]['files']:
            info = parse_fileset(fileset)
            if self.dry_run:
                continue
            try:
                sheet = Sheet.objects.get(volume=vol, sheet_no=info["sheet_number"])
            except Sheet.DoesNotExist:
                sheet = Sheet().create_from_fileset(fileset, vol, fileset_info=info)
            sheets.append(sheet)
        
        return sheets
