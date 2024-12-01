import csv
import json
import importlib
import logging

from django.conf import settings

from ohmg.core.models import Map
from ohmg.places.models import Place

logger = logging.getLogger(__name__)


def get_importer(name, dry_run=False, overwrite=False):
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
    importer_instance = importer_class(dry_run=dry_run, overwrite=overwrite)

    return importer_instance


class BaseImporter:
    required_input = []

    def __init__(self, dry_run: bool = False, verbose: bool = False, overwrite: bool = False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.overwrite = overwrite
        self.input_data = {}
        self.parsed_data = {}

    def validate_input(self, **kwargs):
        missing = []
        for arg in self.required_input:
            if arg not in kwargs:
                error = f"Import operation missing required argumemmnt: {arg}"
                logger.warning(error)
                missing.append(arg)
        return missing

    def validate_parsed(self):
        errors = []
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
            errors.append(f"ERROR: missing parsed output: {missing}")

        for k, v in self.parsed_data.items():
            try:
                if not isinstance(v, output_schema[k]):
                    errors.append(f"incorrect value for parsed output {k}: {v}")
            except KeyError:
                pass

        document_sources = self.parsed_data.get("document_sources", [])

        all_paths = [i["path"] for i in document_sources]
        dupe_paths = list(set([i for i in all_paths if all_paths.count(i) != 1]))
        for dp in dupe_paths:
            print("\n".join(all_paths))
            errors.append(f"ERROR: Document path appears twice in the resources list - {dp}")

        all_numbers = [i["page_number"] for i in document_sources]
        dupe_numbers = list(set([i for i in all_numbers if all_numbers.count(i) != 1]))
        for dp in dupe_numbers:
            errors.append(f"ERROR: Document page number appears twice in the resources list - {dp}")

        return errors

    def parse(self):
        """Parse self.input_data and set the result to self.parsed_data."""

        raise NotImplementedError(
            "This method must be implemented on each " "importer class that inherits from this one."
        )

    def create_map(self):
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

    def run_import(self, **kwargs):
        """Import a single map using the kwargs provided. These keywords are supplied to the
        self.acquire_data()."""

        missing = self.validate_input(**kwargs)
        if missing:
            raise Exception(f"Import operation missing required arg(s): {missing}")

        self.input_data = kwargs
        self.parse()

        errors = self.validate_parsed()
        if errors:
            logger.error(errors)
            raise Exception(errors)

        map = self.create_map()

        return map

    def run_bulk_import(self, csv_file: str):
        """Wraps the main import function by feeding rows from a CSV into it.
        All values in a CSV row are passed to the importer, any irrelevant ones
        will be ignored."""

        with open(csv_file, "r") as o:
            reader = csv.DictReader(o)
            items = [i for i in reader]

        for item in items:
            self.run_import(**item)
