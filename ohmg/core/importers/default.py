import csv
from pathlib import Path

from .base import BaseImporter


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
