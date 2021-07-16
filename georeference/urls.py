from django.urls import path

from .views import (
    iiif2_endpoint,
    split_interface,
    process_cutlines,
    georeference_interface,
    run_georeferencing,
)

urlpatterns = [
    ## IIIF v2.1 paths
    path('iiif/2/<str:docid>/manifest', iiif2_endpoint, {"iiif_object_requested": "manifest"}, name="document_manifest"),
    path('iiif/2/<str:docid>/canvas', iiif2_endpoint, {"iiif_object_requested": "canvas"}, name="document_canvas"),
    path('iiif/2/<str:docid>/resource', iiif2_endpoint, {"iiif_object_requested": "resource"}, name="document_resource"),
    path('iiif/2/<str:docid>/info.json', iiif2_endpoint, {"iiif_object_requested": "info"}, name="document_info"),

    path('run/', run_georeferencing, name="run_georeferencing"),
    path('split/<str:docid>/', split_interface, name="split_interface"),
    path('run-cutlines/<str:docid>/', process_cutlines, name="process_cutlines"),
    # path('run/<str:docid>/', run_georeferencing, name="run_georeferencing"),
    path('<str:docid>/', georeference_interface, name="georeference_interface"),


]
