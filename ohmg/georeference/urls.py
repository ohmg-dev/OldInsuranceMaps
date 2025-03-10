from django.urls import path

from .views import (
    SplitView,
    GeoreferenceView,
    SessionView,
)

urlpatterns = [
    path("split/<int:docid>/", SplitView.as_view(), name="split_view"),
    path(
        "georeference/<int:docid>/",
        GeoreferenceView.as_view(),
        name="georeference_view",
    ),
    path("session/<int:sessionid>/", SessionView.as_view(), name="session_view"),
]
