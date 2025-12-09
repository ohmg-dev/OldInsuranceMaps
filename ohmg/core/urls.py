from django.urls import path

from .views import (
    DocumentView,
    LayersetDerivativeView,
    LayerSetView,
    LayerView,
    MapContributorsView,
    MapListView,
    MapView,
    RegionView,
    ResourceDerivativeView,
)

urlpatterns = [
    path("maps/", MapListView.as_view(), name="map_list"),
    path("map/<str:identifier>", MapView.as_view(), name="map_summary"),
    path(
        "map/<str:identifier>/contributors", MapContributorsView.as_view(), name="map_contributors"
    ),
    path(
        "map/<str:mapid>/<str:category>/<str:derivative>",
        LayersetDerivativeView.as_view(),
        name="map_derivative",
    ),
    path("document/<int:pk>", DocumentView.as_view(), name="document_view"),
    path("region/<int:pk>", RegionView.as_view(), name="region_view"),
    path(
        "region/<int:pk>/<str:derivative>",
        ResourceDerivativeView.as_view(),
        kwargs={"resource": "region"},
        name="region_derivative",
    ),
    path("layer/<int:pk>", LayerView.as_view(), name="layer_view"),
    path(
        "layer/<int:pk>/<str:derivative>",
        ResourceDerivativeView.as_view(),
        kwargs={"resource": "layer"},
        name="layer_derivative",
    ),
    path("layerset/", LayerSetView.as_view(), name="layerset_view"),
    path("layerset/<int:pk>", LayerSetView.as_view(), name="layerset_view"),
]
