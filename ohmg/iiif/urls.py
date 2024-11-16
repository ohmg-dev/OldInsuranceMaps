from django.urls import path

from .views import (
    IIIFResourceView,
    IIIFCanvasView,
)

urlpatterns = [
    path("iiif/resource/<str:regionid>/", IIIFResourceView.as_view(), name="iiif_resource_view"),
    path("iiif/canvas/<str:mapid>/<str:layerset_category>/", IIIFCanvasView.as_view(), name="iiif_canvas_view")
]