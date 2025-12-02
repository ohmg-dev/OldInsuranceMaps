from django.urls import path, register_converter

from ohmg.places.converters import PlaceConverter

from .views import (
    AtlascopeDataView,
    IIIFGCPView,
    IIIFMosaicView,
    IIIFResourceView,
    IIIFSelectorView,
)

register_converter(PlaceConverter, "place-slug")

urlpatterns = [
    path(
        "iiif/selector/<str:layerid>/",
        IIIFSelectorView.as_view(),
        name="iiif_selector_view",
    ),
    path(
        "iiif/gcps/<str:layerid>/",
        IIIFGCPView.as_view(),
        name="iiif_gcps_view",
    ),
    path(
        "iiif/resource/<str:layerid>/",
        IIIFResourceView.as_view(),
        name="iiif_resource_view",
    ),
    path(
        "iiif/mosaic/<str:mapid>/<str:layerset_category>/",
        IIIFMosaicView.as_view(),
        name="iiif_canvas_view",
    ),
    path(
        "atlascope/<str:operation>/<place-slug:place>/",
        AtlascopeDataView.as_view(),
        name="atlascope-data",
    ),
]
