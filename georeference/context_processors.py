from django.conf import settings
from geonode.documents.models import Document
from .models import SplitLink

def georeference_info(request):
    """Global values to pass to templates"""
    child_docs = []
    parent_doc = None
    if request.resolver_match.url_name == 'document_detail':
        docid = request.resolver_match.kwargs['docid']
        links = SplitLink.objects.filter(parent_doc__id=docid)
        for i in links:
            child_docs.append({
                "id": i.child_doc.pk,
                "title": i.child_doc.title,
                "doc_file": i.child_doc.doc_file,
                "detail_url": i.child_doc.detail_url,
                # "thumbnail_url": i.child_doc.thumbnail_url,
            })
    defaults = dict(
        CHILD_DOCUMENTS=child_docs,
        PARENT_DOCUMENT=parent_doc,
        GEOREFERENCE_ENABLED=getattr(
            settings,
            "GEOREFERENCE_ENABLED",
            False),
    )
    return defaults
