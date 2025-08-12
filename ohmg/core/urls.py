from django.urls import path

from .views import (
    MapView,
    MapListView,
    DocumentView,
    RegionView,
    LayerView,
    LayerSetView,
)

urlpatterns = [
    path("maps/", MapListView.as_view(), name="map_list"),
    path("map/<str:identifier>", MapView.as_view(), name="map_summary"),
    path("document/<int:pk>", DocumentView.as_view(), name="document_view"),
    path("region/<int:pk>", RegionView.as_view(), name="region_view"),
    path("layer/<int:pk>", LayerView.as_view(), name="layer_view"),
    path("layerset/", LayerSetView.as_view(), name="layerset_view"),
]
