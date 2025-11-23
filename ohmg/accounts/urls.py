from django.urls import path

from .views import (
    ProfileView,
    verify_prosopo_token,
)

urlpatterns = [
    path("accounts/verify-challenge/", verify_prosopo_token),
    path("profile/<str:username>/", ProfileView.as_view(), name="profile_detail"),
    # path("contributors/", ContributorsView.as_view(), name="contributors"),
]
