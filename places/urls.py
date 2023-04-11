from django.urls import path
from django.views.generic import RedirectView

from .views import (
    Viewer,
    PlaceView,
)

urlpatterns = [
    path('viewer/', RedirectView.as_view(pattern_name='browse', permanent=False), name='viewer_base'),
    path('viewer/<str:place_slug>/', Viewer.as_view(), name='viewer'),
    # path('<str:place_slug>/view/', Viewer.as_view(), name='place_viewer'),
    path('<str:place_slug>/', PlaceView.as_view(), name='place'),
]