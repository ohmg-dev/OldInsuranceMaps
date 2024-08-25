import csv
import json
import importlib
import logging

from django.conf import settings
from django.db import DatabaseError

from ohmg.places.models import Place
from ohmg.loc_insurancemaps.models import Volume
from ohmg.georeference.models import LayerSet, LayerSetCategory
from ohmg.core.models import Document, Map
from ohmg.core.utils import random_alnum

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

        ## remove unused keys for now
        title = self.parsed_data.pop('title')
        creator = self.parsed_data.pop('creator')
        document_sources = self.parsed_data.pop('document_sources')

        existing = Volume.objects.filter(pk=self.parsed_data['identifier'])
        if existing.exists():
            if self.overwrite:
                existing.update(**self.parsed_data)
                volume = existing[0]
                # save to trigger any signals
                volume.save()
            else:
                raise DatabaseError("[ERROR] This map already exists.")
        else:
            volume = Volume.objects.create(**self.parsed_data)

        volume.locales.set([locale])
        volume.update_place_counts()

        ## patch in the kwargs for a Map, until the parser is rebuilt to spit out
        ## fields for the new Map model
        map = Map.objects.create(
            title=volume.__str__(),
            identifier=volume.identifier,
            volume_number=volume.volume_no,
            document_page_type="page",
            year=volume.year,
            month=volume.month,
            loaded_by=volume.loaded_by,
            load_date=volume.load_date,
            document_sources=document_sources,
        )
        map.locales.set(volume.locales.all())
        
        # make sure a main-content layerset exists for this volume
        main_ls, _ = LayerSet.objects.get_or_create(
            category=LayerSetCategory.objects.get(slug="main-content"),
            volume=volume,
            map=map,
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

        errors = self.validate_output(**parsed)
        if errors:
            logger.error(errors)
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
    
    def parse(self):

        print(self.input_data)

        id = self.input_data.get('identifier')
        if id:
            try:
                Volume.objects.get(pk=id)
                if not self.overwrite:
                    raise Exception("A map with the specified identifier already exists.")
            except Volume.DoesNotExist:
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

        # to be removed soon
        city = self.input_data.get('city')
        state = self.input_data.get('state')

        print(file_path)
        
        out = {
            'identifier': id,
            'title': title,
            'year': year,
            'creator': creator,
            'locale': locale,
            'document_sources': [file_path],
            'city': city,
            'state': state,
        }
        return out

    def create_map(self):

        locale = None
        if 'locale' in self.parsed_data:
            locale = Place.objects.get(slug=self.parsed_data.pop('locale'))

        if self.dry_run:
            print(json.dumps(self.parsed_data, indent=2))
            return None
        
        title = self.parsed_data.pop('title')
        creator = self.parsed_data.pop('creator')
        docs = self.parsed_data.pop('document_sources')

        try:
            volume = Volume.objects.get(identifier=self.parsed_data['identifier'])
            if self.overwrite:
                for key, value in self.parsed_data.items():
                    setattr(volume, key, value)
                volume.save()
            else:
                raise Exception("A map with the specified identifier already exists.")
        except Volume.DoesNotExist:
            volume = Volume.objects.create(**self.parsed_data)

        if locale:
            volume.locales.add(locale)

        for doc in docs:
            document = Document().create_from_file(doc, volume=volume)

        volume.update_place_counts()
        # make sure a main-content layerset exists for this volume
        main_ls, _ = LayerSet.objects.get_or_create(
            category=LayerSetCategory.objects.get(slug="main-content"),
            volume=volume,
        )
        return volume