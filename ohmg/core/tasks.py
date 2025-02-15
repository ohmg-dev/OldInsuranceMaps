from ohmg.celeryapp import app
from .models import Map, Document


@app.task
def load_map_documents_as_task(map_id):
    map = Map.objects.get(pk=map_id)
    map.create_documents(get_files=True)
    return map_id


@app.task
def load_document_file_as_task(document_id):
    doc = Document.objects.get(pk=document_id)
    doc.load_file_from_source(overwrite=True)
    return document_id
