from django.urls import path
from django.views.generic import RedirectView

from .views import (
    ProfileView,
    Participants,
)

urlpatterns = [
    path("profile/<str:username>/", ProfileView.as_view(), name="profile_detail"),
    path("profiles/", Participants.as_view(), name="profiles"),
    # make sure old links go to the proper page, use permanent=False for now...
    path("participants/", RedirectView.as_view(pattern_name="profiles", permanent=False)),
    path("participation/", RedirectView.as_view(pattern_name="profiles", permanent=False)),
    path("people/", RedirectView.as_view(pattern_name="profiles", permanent=False)),
]
