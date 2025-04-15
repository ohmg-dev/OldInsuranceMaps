import csv
import json
import importlib
import logging
from pathlib import Path

from django.conf import settings

from ohmg.places.models import Place
from ..utils import random_alnum
from ..models import Map

logger = logging.getLogger(__name__)


class BaseImporter:
    required_input = []

    def __init__(self, dry_run: bool = False, verbose: bool = False, overwrite: bool = False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.overwrite = overwrite
        self.input_data = {}
        self.parsed_data = {}
        self.errors = []

    def validate_input(self, **kwargs):
        missing = []
        for arg in self.required_input:
            if arg not in kwargs:
                error = f"Import operation missing required argumemmnt: {arg}"
                logger.warning(error)
                missing.append(arg)
        return missing

    def check_parsed_data(self):
        output_schema = {
            "identifier": str,
            "title": str,
            "year": (int, type(None)),
            "creator": (str, type(None)),
            "locale": (str, type(None)),
            "document_sources": list,
        }
        missing = [i for i in output_schema.keys() if i not in self.parsed_data.keys()]
        if missing:
            self.errors.append(f"ERROR: missing parsed output: {missing}")

        for k, v in self.parsed_data.items():
            try:
                if not isinstance(v, output_schema[k]):
                    self.errors.append(f"incorrect value for parsed output {k}: {v}")
            except KeyError:
                pass

    def check_identifier(self):
        id = self.parsed_data.get("identifier")
        if id:
            try:
                Map.objects.get(pk=id)
                if not self.overwrite:
                    self.errors.append(f"A map with the identifier '{id}' already exists.")
            except Map.DoesNotExist:
                pass
        else:
            self.parsed_data["identifier"] = random_alnum().upper()

    def check_locale(self):
        locale_slug = self.parsed_data.get("locale")
        try:
            Place.objects.get(slug=locale_slug)
        except Place.DoesNotExist:
            self.errors.append(f"Invalid place slug (doesn't exist): {locale_slug}.")
        except Place.MultipleObjectsReturned:
            self.errors.append(f"Invalid place slug (multiple objects returned): {locale_slug}.")

    def check_document_sources(self):
        document_sources = self.parsed_data.get("document_sources", [])
        all_paths = [i["path"] for i in document_sources]
        dupe_paths = list(set([i for i in all_paths if all_paths.count(i) != 1]))
        for dp in dupe_paths:
            print("\n".join(all_paths))
            self.errors.append(f"ERROR: Document path appears twice in the resources list - {dp}")

        all_numbers = [i["page_number"] for i in document_sources]
        dupe_numbers = list(set([i for i in all_numbers if all_numbers.count(i) != 1]))
        for dp in dupe_numbers:
            self.errors.append(
                f"ERROR: Document page number appears twice in the resources list - {dp}"
            )

    def parse(self):
        """Parse self.input_data and set the result to self.parsed_data."""

        raise NotImplementedError(
            "This method must be implemented on each " "importer class that inherits from this one."
        )

    def create_map(self) -> Map:
        locale = None
        if "locale" in self.parsed_data:
            locale = Place.objects.get(slug=self.parsed_data.pop("locale"))

        if self.dry_run:
            print(json.dumps(self.parsed_data, indent=2))
            return None

        if self.overwrite:
            map, created = Map.objects.get_or_create(identifier=self.parsed_data.get("identifier"))
        else:
            map = Map.objects.create(
                identifier=self.parsed_data.get("identifier"),
            )

        map.title = self.parsed_data.get("title")
        map.creator = self.parsed_data.get("creator")
        map.publisher = self.parsed_data.get("publisher")
        map.year = self.parsed_data.get("year")
        map.month = self.parsed_data.get("month")
        map.volume_number = self.parsed_data.get("volume_number")
        map.document_page_type = self.parsed_data.get("document_page_type", "page")
        map.document_sources = self.parsed_data.get("document_sources", [])
        map.save()

        map.locales.set((locale,))
        map.update_place_counts()
        map.get_layerset("main-content", create=True)

        map.create_documents()
        map.update_item_lookup()

        return map

    def run_import(self, **kwargs) -> Map:
        """Import a single map using the kwargs provided. These keywords are supplied to the
        self.acquire_data()."""

        missing = self.validate_input(**kwargs)
        if missing:
            raise Exception(f"Import operation missing required arg(s): {missing}")

        self.input_data = kwargs
        if self.verbose:
            print("parsing input data:")
            print(json.dumps(self.input_data, indent=2))

        self.parse()

        # run a series of checks, which will add messages to self.errors
        self.check_identifier()
        self.check_locale()
        self.check_document_sources()
        self.check_parsed_data()
        if self.errors:
            for error in self.errors:
                logger.error(error)
                if self.verbose:
                    print(error)
            raise Exception("Errors encountered during map import. See log for more details.")

        if self.verbose:
            print("no errors parsing input.")
            print("parsed input data:")
            print(json.dumps(self.parsed_data, indent=2))

        if not self.dry_run:
            map = self.create_map()
            return map

    def run_bulk_import(self, csv_file: str):
        """Wraps the main import function by feeding rows from a CSV into it.
        All values in a CSV row are passed to the importer, any irrelevant ones
        will be ignored."""

        with open(csv_file, "r") as o:
            reader = csv.DictReader(o)
            items = [i for i in reader]

        csv_parent = Path(csv_file).parent.resolve()
        for item in items:
            ## for 'path' params, treat them as relative to the bulk CSV,
            ## and then resolve to absolute paths.
            if "path" in item:
                item["path"] = str(Path(csv_parent, item["path"]))
            self.run_import(**item)


def get_importer(name, dry_run=False, overwrite=False, verbose=False) -> BaseImporter:
    """Creates an instance of an importer from the class specified in
    settings.py corresponding to the name provided to this function.
    Any kwargs passed to this function are pass directly to the new importer
    instance that is returned."""

    if name not in settings.OHMG_IMPORTERS["map"]:
        return None

    full_path = settings.OHMG_IMPORTERS["map"][name]
    module_path = ".".join(full_path.split(".")[:-1])
    class_name = full_path.split(".")[-1]
    module = importlib.import_module(module_path)
    importer_class = getattr(module, class_name)
    importer_instance = importer_class(dry_run=dry_run, overwrite=overwrite, verbose=verbose)

    return importer_instance
