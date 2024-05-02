from ohmg.celeryapp import app
from ohmg.loc_insurancemaps.models import Volume

@app.task
def load_docs_as_task(volume_id):
    volume = Volume.objects.get(pk=volume_id)
    volume.load_sheet_docs()

