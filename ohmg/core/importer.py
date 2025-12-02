import csv
import importlib
import json
import logging
from pathlib import Path
from warnings import warn

from django.conf import settings

from ohmg.places.models import Place

from .models import Map
from .utils import random_alnum

logger = logging.getLogger(__name__)


def get_importer(
    name, dry_run=False, overwrite=False, verbose=False, skip_existing=False
) -> "BaseImporter":
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
    importer_instance = importer_class(
        dry_run=dry_run, overwrite=overwrite, verbose=verbose, skip_existing=skip_existing
    )

    return importer_instance


class BaseImporter:
    required_input = []

    def __init__(
        self,
        dry_run: bool = False,
        verbose: bool = False,
        overwrite: bool = False,
        skip_existing: bool = False,
    ):
        self.dry_run = dry_run
        self.verbose = verbose
        self.overwrite = overwrite
        self.skip_existing = skip_existing
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
        exists = False
        id = self.parsed_data.get("identifier")
        if id:
            try:
                Map.objects.get(pk=id)
                exists = True
                if not self.overwrite:
                    if self.skip_existing:
                        warn(f"Skipping map {id}, already in system.")
                    else:
                        self.errors.append(f"A map with the identifier '{id}' already exists.")
            except Map.DoesNotExist:
                pass
        else:
            self.parsed_data["identifier"] = random_alnum().upper()

        return exists

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
        map_exists = self.check_identifier()
        if map_exists and self.skip_existing:
            logger.warning(
                f"a map with the id {self.parsed_data['identifier']} already exists, skipping load"
            )
            return None
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

        with open(csv_file, "r", encoding="utf-8-sig") as o:
            reader = csv.DictReader(o)
            items = [i for i in reader]

        csv_parent = Path(csv_file).parent.resolve()
        for item in items:
            ## for 'path' params, treat them as relative to the bulk CSV,
            ## and then resolve to absolute paths.
            if "path" in item:
                item["path"] = str(Path(csv_parent, item["path"]))
            self.run_import(**item)


class DefaultImporter(BaseImporter):
    """Default Importer

    This is the default operation for loading a new Map. A single image file can be provided,
    or a CSV that has a list of one or more files. Paths in the CSV

    Required opts:

        path:       path/to/image.tif OR path/to/file-list.csv
        year:       year of publication
        locale:     slug for locale

    Optional opts:

        identifier: will be used as pk for this map
        title:      will be "Untitled map" if not provided
        creator:    name of creator for map
    """

    required_input = [
        "path",
        "year",
        "locale",
    ]

    def parse(self):
        path = self.input_data.get("path")

        # if csv provided, it will have the list of files in it
        document_sources = []
        if path.endswith(".csv"):
            csv_path = Path(path)
            with open(path, "r") as o:
                reader = csv.DictReader(o)
                for n, row in enumerate(reader, start=1):
                    # treat paths in the CSV as relative to the CSV itself
                    doc_path = row.get("path", "")
                    if doc_path:
                        doc_path = Path(csv_path.parent, doc_path)
                        doc_path = str(doc_path.resolve())
                    document_sources.append(
                        {
                            "path": doc_path,
                            "iiif_info": row.get("iiif_info", ""),
                            "page_number": row.get("page_number", str(n)),
                        }
                    )
        # otherwise, this is the single file
        else:
            document_sources.append(
                {
                    "path": path,
                    "iiif_info": self.input_data.get("iiif_info", ""),
                    "page_number": self.input_data.get("page_number", "1"),
                }
            )

        self.parsed_data = {
            "locale": self.input_data["locale"],
            "document_sources": document_sources,
            "year": int(self.input_data["year"]),
            "identifier": self.input_data.get("identifier"),
            "title": self.input_data.get("title", "Untitled map"),
            "creator": self.input_data.get("creator", "n/a"),
        }
