from django.urls import path

from .views import (
    iiif2_endpoint,
    SplitView,
    TrimView,
    GeoreferenceView,
    OverviewView,
)

urlpatterns = [
    ## IIIF v2.1 paths
    path('iiif/2/<str:docid>/manifest', iiif2_endpoint, {"iiif_object_requested": "manifest"}, name="document_manifest"),
    path('iiif/2/<str:docid>/canvas', iiif2_endpoint, {"iiif_object_requested": "canvas"}, name="document_canvas"),
    path('iiif/2/<str:docid>/resource', iiif2_endpoint, {"iiif_object_requested": "resource"}, name="document_resource"),
    path('iiif/2/<str:docid>/info.json', iiif2_endpoint, {"iiif_object_requested": "info"}, name="document_info"),
    ## action urls
    path('split/<int:docid>/', SplitView.as_view(), name="split_view"),
    path('trim/<str:layeralternate>/', TrimView.as_view(), name="trim_view"),
    path('georeference/<int:docid>/', GeoreferenceView.as_view(), name="georeference_view"),

    path('<str:objectid>', OverviewView.as_view(), name="overview_view"),
]
