from django.urls import path

from .views import (
    ProfileView,
)

urlpatterns = [
    path("profile/<str:username>/", ProfileView.as_view(), name="profile_detail"),
]
