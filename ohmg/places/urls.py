from django.urls import path
from django.views.generic import RedirectView

from .views import (
    PlaceView,
)

urlpatterns = [
    path('<str:place_slug>/', PlaceView.as_view(), name='place'),
]