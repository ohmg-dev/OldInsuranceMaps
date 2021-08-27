from django.urls import path

from .views import (
    iiif2_endpoint,
    split_interface,
    run_splitting,
    trim_interface,
    run_trimming,
    georeference_interface,
    run_georeferencing,
    document_progress,
)

urlpatterns = [
    ## IIIF v2.1 paths
    path('iiif/2/<str:docid>/manifest', iiif2_endpoint, {"iiif_object_requested": "manifest"}, name="document_manifest"),
    path('iiif/2/<str:docid>/canvas', iiif2_endpoint, {"iiif_object_requested": "canvas"}, name="document_canvas"),
    path('iiif/2/<str:docid>/resource', iiif2_endpoint, {"iiif_object_requested": "resource"}, name="document_resource"),
    path('iiif/2/<str:docid>/info.json', iiif2_endpoint, {"iiif_object_requested": "info"}, name="document_info"),
    ## action urls
    path('status/<str:docid>', document_progress, name="document_progress"),
    path('split/<str:docid>/', split_interface, name="split_interface"),
    path('split/<str:docid>/run', run_splitting, name="run_splitting"),
    path('trim/<str:docid>/', trim_interface, name="trim_interface"),
    path('trim/<str:docid>/run', run_trimming, name="run_trimming"),

    path('georeference/<str:docid>/', georeference_interface, name="georeference_interface"),
    path('georeference/<str:docid>/run/', run_georeferencing, name="run_georeferencing"),
    
]
