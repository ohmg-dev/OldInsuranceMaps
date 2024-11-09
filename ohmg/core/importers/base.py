import csv
import json
import importlib
import logging

from django.conf import settings

from ohmg.core.models import Map
from ohmg.core.utils import random_alnum
from ohmg.places.models import Place

logger = logging.getLogger(__name__)

def get_importer(name, dry_run=False, overwrite=False):
    """ Creates an instance of an importer from the class specified in
    settings.py corresponding to the name provided to this function.
    Any kwargs passed to this function are pass directly to the new importer
    instance that is returned."""

    if name not in settings.OHMG_IMPORTERS['map']:
        return None

    full_path = settings.OHMG_IMPORTERS['map'][name]
    module_path = ".".join(full_path.split(".")[:-1])
    class_name = full_path.split(".")[-1]
    module  = importlib.import_module(module_path)
    importer_class = getattr(module, class_name)
    importer_instance = importer_class(dry_run=dry_run, overwrite=overwrite)

    return importer_instance


class BaseImporter():

    required_input = []

    def __init__(self, dry_run: bool=False, verbose: bool=False, overwrite: bool=False):

        self.dry_run = dry_run
        self.verbose = verbose
        self.overwrite = overwrite
        self.input_data = {}
        self.parsed_data = {}

    def validate_input(self, **kwargs):

        errors = []
        for arg in self.required_input:
            if arg not in kwargs:
                error = f"Import operation missing required argument: {arg}"
                logger.warning(error)
                errors.append(error)
        return errors
    
    def validate_parsed(self):

        errors = []
        output_schema = {
            'identifier': str,
            'title': str,
            'year': (int, type(None)),
            'creator': (str, type(None)),
            'locale': (str, type(None)),
            'document_sources': list,
        }
        missing = [i for i in output_schema.keys() if i not in self.parsed_data.keys()]
        if missing:
            errors.append(f"missing parsed output: {missing}")

        for k, v in self.parsed_data.items():
            try:
                if not isinstance(v, output_schema[k]):
                   errors.append(f"incorrect value for parsed output {k}: {v}") 
            except KeyError:
                pass
        return errors

    def parse(self):
        """ Parse self.input_data and set the result to self.parsed_data. """

        raise NotImplementedError("This method must be implemented on each "\
            "importer class that inherits from this one.")

    def create_map(self):

        locale = None
        if 'locale' in self.parsed_data:
            locale = Place.objects.get(slug=self.parsed_data.pop('locale'))

        if self.dry_run:
            print(json.dumps(self.parsed_data, indent=2))
            return None

        map = Map.objects.create(
            title=self.parsed_data.get("title"),
            identifier=self.parsed_data.get("identifier"),
            creator=self.parsed_data.get("creator"),            
            publisher=self.parsed_data.get("publisher"),            
            year=self.parsed_data.get("year"),
            month=self.parsed_data.get("month"),
            volume_number=self.parsed_data.get("volume_number"),
            document_page_type=self.parsed_data.get('document_page_type', "page"),
            document_sources=self.parsed_data.get("document_sources", []),
        )
        map.locales.set((locale,))
        map.update_item_lookup()
        map.update_place_counts()
        map.get_layerset('main-content', create=True)

        return map

    def run_import(self, **kwargs):
        """ Import a single map using the kwargs provided. These keywords are supplied to the
        self.acquire_data(). """

        errors = self.validate_input(**kwargs)
        if errors:
            raise Exception("Import operation missing required arg(s), check logs for more info.")

        self.input_data = kwargs
        self.parse()

        errors = self.validate_parsed()
        if errors:
            logger.error(errors)
            raise Exception(errors)

        map = self.create_map()

        return map
    
    def run_bulk_import(self, csv_file: str):
        """ Wraps the main import function by feeding rows from a CSV into it. 
        All values in a CSV row are passed to the importer, any irrelevant ones
        will be ignored. """

        with open(csv_file, "r") as o:
            reader = csv.DictReader(o)
            items = [i for i in reader]

        for item in items:
            self.run_import(**item)


class SingleFileImporter(BaseImporter):
    """Single File Importer
-------------
Use this importer to create a new Map object with a single file in it. The following
opts are supported:

    file_name: path/to/file.tif
    (incomplete list so far...\)
"""
    
    def parse(self):

        print(self.input_data)

        id = self.input_data.get('identifier')
        if id:
            try:
                Map.objects.get(pk=id)
                if not self.overwrite:
                    raise Exception("A map with the specified identifier already exists.")
            except Map.DoesNotExist:
                pass
        else:
            id = random_alnum().upper()

        file_path = self.input_data.get('file_path')
        title = self.input_data.get('title', "test map")
        year = self.input_data.get('year')
        if year:
            year = int(year)
        creator = self.input_data.get('creator')
        locale = self.input_data.get('locale')

        print(file_path)
        
        self.parsed_data = {
            'identifier': id,
            'title': title,
            'year': year,
            'creator': creator,
            'locale': locale,
            'document_sources': [file_path],
        }
