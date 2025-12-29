from ohmg.conf.celery import app

from .models import Document, Map


@app.task
def load_map_documents_as_task(map_id, username):
    map = Map.objects.get(pk=map_id)
    map.load_all_document_files(username)
    return map_id


@app.task
def load_document_file_as_task(document_id, username):
    doc = Document.objects.get(pk=document_id)
    doc.load_file_from_source(username, overwrite=True)
    return document_id
