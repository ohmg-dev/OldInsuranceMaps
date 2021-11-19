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

                # set defaults that will pass through quietly for irrelevant items (i.e. Maps)
                item['georeference_status'] = "n/a"
                item['georeference_links'] = []

                # create the appropriate proxy model based on item type
                try:
                    resource_type = item['detail_url'].split("/")[1].rstrip("s")
                except IndexError:
                    resource_type = None
                proxy = None
                if resource_type == "document":
                    proxy = DocumentProxy(item['id'])
                if resource_type == "layer":
                    proxy = LayerProxy(item['id'])
                
                if proxy is not None:
                    status = proxy.status
                    proxy_urls = proxy.get_extended_urls()
                    links = [{
                        "title": "Progress Page",
                        "icon": "fa-list-ol",
                        "url": proxy_urls['progress_page'],
                    }]
                    if status == "unprepared":
                        links.append({
                            "title": "Prepare Document",
                            "icon": "fa-cut",
                            "url": proxy_urls['split'],
                        })
                    if status == "prepared":
                        links.append({
                            "title": "Georeference Document",
                            "icon": "fa-map-pin",
                            "url": proxy_urls['georeference'],
                        })
                    if status == "georeferenced":
                        links.append({
                            "title": "Edit Georeferencing",
                            "icon": "fa-map-pin",
                            "url": proxy_urls['georeference'],
                        })
                        if resource_type == "document":
                            links.append({
                                "title": "Go To Georeferenced Layer",
                                "icon": "fa-image",
                                "url": proxy_urls['layer_detail'],
                            })
                        if resource_type == "layer":
                            links.append({
                                "title": "Trim Layer",
                                "icon": "fa-crop",
                                "url": proxy_urls['trim'],
                            })
                            links.append({
                                "title": "Go To Original Document",
                                "icon": "fa-newspaper-o",
                                "url": proxy_urls['document_detail'],
                            })

                    item['georeference_links'] = links
                    item['georeferencing_status'] = status

            response._container = [json.dumps(data).encode()]
        return response
