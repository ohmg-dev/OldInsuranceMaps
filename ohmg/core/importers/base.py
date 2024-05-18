import csv
import json
import importlib
import logging

from django.conf import settings

from ohmg.places.models import Place
from ohmg.loc_insurancemaps.models import Volume
from ohmg.georeference.models import AnnotationSet, SetCategory
from ohmg.core.utils import random_alnum

logger = logging.getLogger(__name__)

def get_importer(name, dry_run=False):
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
    importer_instance = importer_class(dry_run=dry_run)

    return importer_instance


class BaseImporter():

    required_input = []

    def __init__(self, dry_run: bool=False, verbose: bool=False):

        self.dry_run = dry_run
        self.verbose = verbose
        self.input_data = {}
        self.parsed_data = {}

    def validate_input(self, **kwargs):

        errors = []
        for arg in self.required_input:
            if arg not in kwargs:
                error = f"Import operation missing required argument: {arg}"
                logger.warn(error)
                errors.append(error)
        return errors
    
    def validate_output(self, **kwargs):

        errors = []
        output_schema = {
            'title': str,
            'year': (int, type(None)),
            'creator': (str, type(None)),
            'locale': (str, type(None)),
            'document_sources': list,
        }
        missing = [i for i in output_schema.keys() if i not in kwargs.keys()]
        if missing:
            errors.append(f"missing props: {missing}")

        for k, v in kwargs.items():
            try:
                if not isinstance(v, output_schema[k]):
                   errors.append(f"incorrect value for {k}: {v}") 
            except KeyError:
                pass
        return errors

    def parse(self, **kwargs):
        """ This method must parse whatever the input kwargs are, and set the
        result to self.parsed_data. Default behavior leaves the input data 
        unchanged. The structure of the o"""

        raise NotImplementedError("This method must be implemented on each"\
            "importer class that inherits from this one.")

    def create_map(self):

        locale = None
        if 'locale' in self.parsed_data:
            locale = Place.objects.get(slug=self.parsed_data.pop('locale'))

        if self.dry_run:
            print(json.dumps(self.parsed_data, indent=2))
            return None
        volume = Volume.objects.create(**self.parsed_data)

        if locale:
            volume.locales.add(locale)

        volume.update_place_counts()
        # make sure a main-content layerset exists for this volume
        main_ls, _ = AnnotationSet.objects.get_or_create(
            category=SetCategory.objects.get(slug="main-content"),
            volume=volume,
        )
        return volume

    def run_import(self, **kwargs):
        """ Import a single map using the kwargs provided. These keywords are supplied to the
        self.acquire_data(). """

        errors = self.validate_input(**kwargs)
        if errors:
            raise Exception("Import operation missing required arg(s), check logs for more info.")

        self.input_data = kwargs
        parsed = self.parse()

        print(parsed)

        errors = self.validate_output(**parsed)
        if errors:
            print(errors)
            raise Exception('errors')
        
        self.parsed_data = parsed
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
    
    def parse(self, **kwargs):

        id = kwargs.get('identifier')
        if id:
            try:
                Volume.objects.get(pk=id)
                raise Exception("A map with the specified identifier already exists.")
            except Volume.DoesNotExist:
                pass
        else:
            id = random_alnum()
        
        out = {
            'identifier': id,
            'title': "test map"
        }
        return out
