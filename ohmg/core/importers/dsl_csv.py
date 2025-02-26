import csv
from pathlib import Path

from ..utils import random_alnum
from ..models import Map
from .base import BaseImporter


class DSLFileImporter(BaseImporter):
    """DSL File Importer
    -------------
    Use this importer to create a new Map object with multiple Documents, as defined in a provided
    CSV file. The input CSV must have one line per Document, with columns 'filename' and
    'page_number'. The name of the CSV should be formatted as such:

    <locale-slug>_<year>_<volume_number (optional)>.csv

        csv-path: path/to/file.csv
        files-dir: path/to/directory/with/files
        title: title of map

    """

    required_input = [
        "csv-path",
        "files-dir",
        "title",
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

        title = self.input_data.get("title", "test map")

        parts = Path(self.input_data.get("csv-path")).name.split("_")
        locale = parts[0]
        year = int(parts[1])
        volume_number = parts[2] if len(parts) == 3 else None

        if year:
            year = int(year)
        creator = self.input_data.get("creator")
        locale = self.input_data.get("locale")

        with open(self.input_data.get("csv-path"), "r") as o:
            reader = csv.DictReader(o)
            rows = [i for i in reader]

        document_sources = []
        for row in rows:
            fp = Path(self.input_data.get("files-dir"), row["filename"])
            if not fp.is_file():
                raise Exception(f"can't find expected document file: {fp}")

            document_sources.append(
                {
                    "path": fp,
                    "iiif_info": None,
                    "page_number": row["page_number"],
                }
            )

        self.parsed_data = {
            "identifier": id,
            "title": title,
            "year": year,
            "creator": creator,
            "locale": locale,
            "volume_number": volume_number,
            "document_sources": document_sources,
        }
