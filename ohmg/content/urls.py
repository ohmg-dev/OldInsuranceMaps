from django.urls import path

from .views import (
    ItemView,
    VirtualResourceView,
)

urlpatterns = [
    path('item/<str:identifier>', ItemView.as_view(), name="resource_detail"),
    path('resource/<int:pk>', VirtualResourceView.as_view(), name="resource_detail"),
]
