from django.urls import path

from .views import (
    PlaceView,
)

urlpatterns = [
    path('<str:place_slug>/', PlaceView.as_view(), name='place'),
]