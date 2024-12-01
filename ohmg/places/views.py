from django.shortcuts import render, get_object_or_404
from django.views import View

from ohmg.core.api.schemas import PlaceFullSchema
from ohmg.core.context_processors import generate_ohmg_context
from ohmg.places.models import Place


class PlaceView(View):
    def get(self, request, place_slug):
        p = get_object_or_404(Place.objects.prefetch_related(), slug=place_slug)

        context_dict = {
            "params": {
                "CONTEXT": generate_ohmg_context(request),
                "PAGE_NAME": "place",
                "PARAMS": {
                    "PLACE": PlaceFullSchema.from_orm(p).dict(),
                },
            }
        }
        return render(request, "index.html", context=context_dict)
