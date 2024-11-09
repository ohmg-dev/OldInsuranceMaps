from ohmg.celeryapp import app
from .models import Map

@app.task
def load_map_documents_as_task(map_id):
    map = Map.objects.get(pk=map_id)
    map.create_documents(get_files=True)
    return map_id
