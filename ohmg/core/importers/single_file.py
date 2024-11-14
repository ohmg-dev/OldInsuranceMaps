
from ..utils import random_alnum
from ..models import Map
from .base import BaseImporter

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
                Map.objects.get(pk=id)
                if not self.overwrite:
                    raise Exception("A map with the specified identifier already exists.")
            except Map.DoesNotExist:
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

        print(file_path)
        
        self.parsed_data = {
            'identifier': id,
            'title': title,
            'year': year,
            'creator': creator,
            'locale': locale,
            'document_sources': [file_path],
        }
