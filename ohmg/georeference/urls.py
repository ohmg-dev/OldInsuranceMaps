from django.urls import path

from .views import GeoreferenceView, JobView, SessionView, SplitView

urlpatterns = [
    path("split/", SplitView.as_view(), name="base_split_view"),
    path("split/<int:docid>/", SplitView.as_view(), name="split_view"),
    path(
        "georeference/<int:docid>/",
        GeoreferenceView.as_view(),
        name="georeference_view",
    ),
    path("session/<int:sessionid>/", SessionView.as_view(), name="session_view"),
    path("job/<int:jobid>/", JobView.as_view(), name="job_view"),
]
