from django.conf import settings
from .utils.enumerations import STATE_CHOICES

def lc_svelte_params(request):
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
    lc_svelte = {
        "lc_svelte_params": {
            "STATE_CHOICES": STATE_CHOICES
        }
    }
    return lc_svelte
