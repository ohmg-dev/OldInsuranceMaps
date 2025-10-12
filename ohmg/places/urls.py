from django.urls import path, register_converter

from .converters import PlaceConverter
from .views import (
    PlaceView,
    Viewer,
)

register_converter(PlaceConverter, "place-slug")

urlpatterns = [
    path("<place-slug:place>/", PlaceView.as_view(), name="place"),
    path("viewer/<place-slug:place>/", Viewer.as_view(), name="viewer"),
]
