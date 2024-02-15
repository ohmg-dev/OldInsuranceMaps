from django.urls import path
from django.views.generic import RedirectView

from .views import (
    MapSummary,
    VirtualResourceView,
)

urlpatterns = [
    path('map/<str:identifier>', MapSummary.as_view(), name="map_summary"),
    path('resource/<int:pk>', VirtualResourceView.as_view(), name="resource_detail"),
    # temporary overlap here, ultimately will remove all /loc/ and /item/ urls
    path('item/<str:identifier>', RedirectView.as_view(pattern_name='map_summary', permanent=True), name="volume_summary"),
    path('loc/volumes/', RedirectView.as_view(pattern_name='search', permanent=True), name='volumes_list'),
    path('loc/<str:identifier>/', RedirectView.as_view(pattern_name='map_summary', permanent=True), name="volume_summary"),
    path('loc/trim/<str:identifier>/', RedirectView.as_view(pattern_name='map_summary', permanent=True), name="volume_trim"),
]
