import logging

from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views import View

from ohmg.context_processors import generate_ohmg_context
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
                    "CONTEXT": generate_ohmg_context(request),
                    "PAGE_NAME": 'place',
                    "PARAMS": {
                        "PLACE": place,
                    }
                }
            }
            return render(
                request,
                "index.html",
                context=context_dict
            )
