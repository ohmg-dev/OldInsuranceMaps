import json

from .proxy_models import (
    DocumentProxy,
    LayerProxy,
)

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
            '/api/base/',
        ]
        if request.path in api_paths:
            data = json.loads(response._container[0].decode("utf-8"))
            for item in data['objects']:

                # use the detail url to get the type of item
                item['type'] = item['detail_url'].split("/")[1].rstrip("s")

                # set defaults that will pass through quietly for irrelevant items (i.e. Maps)
                item['georeferencing_status'] = "n/a"
                item['urls'] = {"progress_page": ''}

                # generate urls for documents
                if item['type'] == "document":
                    document = DocumentProxy(item['id'])
                    item['georeferencing_status'] = document.status
                    item['urls'].update(document.get_extended_urls())

                # generate urls for layers
                if item['type'] == "layer":
                    layer = LayerProxy(item['id'])
                    item['georeferencing_status'] = layer.status
                    item['urls'].update(layer.get_extended_urls())

            response._container = [json.dumps(data).encode()]
        return response
