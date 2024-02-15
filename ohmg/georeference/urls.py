from django.urls import path

from .views import (
    SplitView,
    GeoreferenceView,
    MultiMaskView
)

urlpatterns = [
    path('split/<int:docid>/', SplitView.as_view(), name="split_view"),
    path('georeference/<int:docid>/', GeoreferenceView.as_view(), name="georeference_view"),
    path('trim/<str:volumeid>/', MultiMaskView.as_view(), name="volume_trim"),
]
