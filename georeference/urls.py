from django.urls import path

from .views import (
    SplitView,
    TrimView,
    GeoreferenceView,
    SummaryJSON,
)

urlpatterns = [
    path('split/<int:docid>/', SplitView.as_view(), name="split_view"),
    path('georeference/<int:docid>/', GeoreferenceView.as_view(), name="georeference_view"),
    path('trim/<str:layeralternate>/', TrimView.as_view(), name="trim_view"),
    path('georeference-info/<str:resourceid>', SummaryJSON.as_view(), name="georeference_info")
]
