import json
from django.urls import reverse

from geonode.layers.models import Layer
from geonode.documents.models import Document

from .utils import get_layer_from_document, get_document_from_layer

class GeoreferenceMiddleware:
    """This middleware injects a little bit of extra information into the
    Layer and Document objects that are returned to the search page. This info
    is used to determine which georeferencing-related links and text to place
    in the objects search results box."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        response = self.get_response(request)
        print(request.path)
        api_paths = [
            '/api/documents/',
            '/api/layers/',
        ]
        if request.path in api_paths:
            data = json.loads(response._container[0].decode("utf-8"))
            for item in data['objects']:

                # first use the detail url to get the type of item
                if "layer" in item['detail_url']:
                    item['type'] = 'layer'
                if "document" in item['detail_url']:
                    item['type'] = 'document'

                # set the status (same for all items)
                if "prepared" in item['tkeywords']:
                    item['georeferencing_status'] = "Prepared"
                elif "unprepared" in item['tkeywords']:
                    item['georeferencing_status'] = "Unprepared"
                elif "georeferenced" in item['tkeywords']:
                    item['georeferencing_status'] = "Georeferenced"

                # generate urls for documents
                if item['type'] == "document":
                    item['split_url'] = reverse("split_view", args=(item['id'],))
                    item['georeference_url'] = reverse("georeference_view", args=(item['id'],))
                    if item['georeferencing_status'] == "Georeferenced":
                        document = Document.objects.get(pk=item['id'])
                        layer = get_layer_from_document(document)
                        item['layer_url'] = reverse("layer_detail", args=(layer.alternate,))

                # generate urls for layers
                if item['type'] == "layer":
                    layer = Layer.objects.get(pk=item['id'])
                    document = get_document_from_layer(layer)
                    item['document_url'] = reverse("document_detail", args=(document.pk, ))
                    item['georeference_url'] = reverse("georeference_view", args=(document.pk, ))

            response._container = [json.dumps(data).encode()]
        return response
