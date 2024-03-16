import logging

from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views import View

from ohmg.utils import get_internal_routes
from ohmg.places.models import Place

logger = logging.getLogger(__name__)


class PlaceView(View):

    def get(self, request, place_slug):

        f = request.GET.get("f", None)
        p = get_object_or_404(Place, slug=place_slug)
        place = p.serialize()

        if f == "json":
            return JsonResponse({
                "PLACE": place,
            })

        else:
            context_dict = {
                "params": {
                    "PAGE_NAME": 'place',
                    "PARAMS": {
                        "ROUTES": get_internal_routes(),
                        "PLACE": place,
                    }
                }
            }
            return render(
                request,
                "index.html",
                context=context_dict
            )
