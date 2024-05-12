import json
import importlib
import logging

from django.conf import settings

from ohmg.places.models import Place
from ohmg.loc_insurancemaps.models import Volume
from ohmg.georeference.models import AnnotationSet, SetCategory

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

    required_args = []

    def __init__(self, dry_run: bool=False, verbose: bool=False):

        self.dry_run = dry_run
        self.verbose = verbose
        self.data = {}
        self.parsed_data = {}

    def check_args(self, **kwargs):

        errors = []
        for arg in self.required_args:
            if arg not in kwargs:
                error = f"Import operation missing required argument: {arg}"
                logger.warn(error)
                errors.append(error)
        return errors

    def acquire_data(self, **kwargs):
        """ This method can be passed any arguments that are needed. It must 
        generate a dict and set that dict to self.data, which will then be 
        parsed by self.data to self.parse().
        """
        raise NotImplementedError("Must be defined downstream.")

    def parse_data(self, **kwargs):
        """ This method will use whatever is in self.data, parse it, and set
        the result to self.parsed_data. Default behavior leaves the input
        data unchanged."""

        self.parsed_data = self.data

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

        errors = self.check_args(**kwargs)
        if errors:
            raise Exception("Import operation missing required arg(s), check logs for more info.")
        self.acquire_data(**kwargs)
        self.parse_data(**kwargs)

        map = self.create_map()

        return map
