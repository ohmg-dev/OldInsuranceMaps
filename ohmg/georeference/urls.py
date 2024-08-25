from django.urls import path

from .views import (
    SplitView,
    GeoreferenceView,
    LayerSetView,
)

urlpatterns = [
    path('split/<int:docid>/', SplitView.as_view(), name="split_view"),
    path('georeference/<int:docid>/', GeoreferenceView.as_view(), name="georeference_view"),
    path('annotation-set/', LayerSetView.as_view(), name="annotation_set_view")
]
