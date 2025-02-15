from django.urls import path

from .views import (
    IIIFSelectorView,
    IIIFResourceView,
    IIIFGCPView,
    IIIFCanvasView,
)

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
        IIIFCanvasView.as_view(),
        name="iiif_canvas_view",
    ),
]
