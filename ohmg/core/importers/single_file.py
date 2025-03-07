from ..utils import random_alnum
from ..models import Map
from .base import BaseImporter


class SingleFileImporter(BaseImporter):
    """Single File Importer

    Use this importer to create a new Map object with a single file in it.

    Required opts:

        file-path:  path/to/file.tif
        year:       year of publication

    """

    required_input = [
        "file-path",
        "year",
        "locale",
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

        file_paths = self.input_data.get("file-path").split(";")
        title = self.input_data.get("title", "test map")
        year = self.input_data.get("year")
        if year:
            year = int(year)
        creator = self.input_data.get("creator")
        locale = self.input_data.get("locale")

        document_sources = [
            {
                "path": fp,
                "iiif_info": None,
                "page_number": None if len(file_paths) == 1 else i,
            }
            for i, fp in enumerate(file_paths, start=1)
        ]

        self.parsed_data = {
            "identifier": id,
            "title": title,
            "year": year,
            "creator": creator,
            "locale": locale,
            "document_sources": document_sources,
        }
