import json
from georeference.utils import full_reverse

from .models import get_volume

class LOCMiddleware:
    """This middleware injects a little bit of extra information into the
    Layer and Document objects that are returned to the search page. This info
    is used to determine which georeferencing-related links and text to place
    in the item's search results box."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        response = self.get_response(request)
        path = request.path
        api_paths = [
            '/api/documents/',
            '/api/layers/',
            '/api/base/',
        ]
        if path in api_paths:
            data = json.loads(response._container[0].decode("utf-8"))
            for item in data['objects']:
                res_id = item.get('id')
                try:
                    resource_type = item['detail_url'].split("/")[1].rstrip("s")
                except IndexError:
                    item['volume_title'] = ""
                    item['volume_url'] = ""
                    continue

                if res_id is not None and resource_type in ["document", "layer"]:
                    vol = get_volume(resource_type, res_id)
                    item['volume_title'] = vol.__str__()
                    item['volume_url'] = full_reverse('volume_summary', args=(vol.pk,))

            response._container = [json.dumps(data).encode()]
        return response