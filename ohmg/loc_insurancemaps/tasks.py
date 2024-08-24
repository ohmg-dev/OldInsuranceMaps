from ohmg.celeryapp import app
from ohmg.loc_insurancemaps.models import Volume
from ohmg.core.models import Map

@app.task
def load_docs_as_task(volume_id):
    volume = Volume.objects.get(pk=volume_id)
    volume.load_sheet_docs()

@app.task
def load_map_documents_as_task(map_id):
    map = Map.objects.get(pk=map_id)
    map.create_documents(get_files=True)