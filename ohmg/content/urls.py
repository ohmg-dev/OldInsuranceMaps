from django.urls import path

from .views import (
    ResourceView,
)

urlpatterns = [
    path('resource/<int:pk>', ResourceView.as_view(), name="resource_detail"),
]
