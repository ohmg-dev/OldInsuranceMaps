import csv
import logging
from pathlib import Path

from ..utils import random_alnum, STATE_ABBREV, STATE_POSTAL
from ..models import Map
from .base import BaseImporter

logger = logging.getLogger(__name__)


class DSLFileImporter(BaseImporter):
    """DSL File Importer
    -------------
    Use this importer to create a new Map object with multiple Documents, based
    on content exported from an external system used by the DSL. The input CSV must
    have one line per Document, with columns 'filename' and 'page_number'.
    Filenames must match files present in a directory with the same name as the
    CSV.

    The name of the CSV (and corresponding file folder) must be constructed like:

        <locale-slug>_<year>_<volume_number (optional)>.csv

    Required opts:

        csv-path: path/to/file.csv
    """

    required_input = [
        "csv-path",
    ]

    def parse(self):
        print(self.input_data)

        id = self.input_data.get("identifier")
        if id:
            try:
                Map.objects.get(pk=id)
                if not self.overwrite:
                    raise Exception("A map with the specified identifier already exists.")
            except Map.DoesNotExist:
                pass
        else:
            id = random_alnum().upper()

        parts = Path(self.input_data.get("csv-path")).stem.split("_")
        locale = parts[0]
        year = int(parts[1])
        volume_number = parts[2] if len(parts) == 3 else None

        postal_rev = {v: k for k, v in STATE_POSTAL.items()}
        city_words = locale.split("-")[:-1]
        city = " ".join([i.capitalize() for i in city_words])
        po = locale.split("-")[-1]
        abbr = STATE_ABBREV[postal_rev[po]]

        title = f"Sanborn Map of {city}, {abbr}, {year}{', Vol. '+volume_number if volume_number else ''}"

        csv_path = Path(self.input_data.get("csv-path")).resolve().absolute()
        with open(csv_path, "r") as o:
            reader = csv.DictReader(o)
            rows = [i for i in reader]

        files_dir = Path(csv_path.parent.absolute(), csv_path.stem)
        document_sources = []
        for row in rows:
            fp = Path(files_dir, row["filename"])
            if not fp.is_file():
                logger.warn(f"{csv_path}: can't find expected document file: {fp}")

            document_sources.append(
                {
                    "path": str(fp.absolute()),
                    "iiif_info": None,
                    "page_number": row["page_number"],
                }
            )

        self.parsed_data = {
            "identifier": id,
            "title": title,
            "year": year,
            "creator": "Sanborn Map Company",
            "locale": locale,
            "volume_number": volume_number,
            "document_sources": document_sources,
        }
        exit()
