from django.urls import include, path
from django.views.generic import RedirectView

from .views import OHMGSignupView, ProfilesView, ProfileView

urlpatterns = [
    ## overwrite the default allauth signup view here
    path("account/signup/", OHMGSignupView.as_view(), name="account_signup"),
    path("account/", include("allauth.urls")),
    path("profile/<str:username>/", ProfileView.as_view(), name="profile_detail"),
    path("profiles/", ProfilesView.as_view(), name="profiles"),
    ## these are all past versions of the profiles page
    path("participants/", RedirectView.as_view(pattern_name="profiles", permanent=False)),
    path("participation/", RedirectView.as_view(pattern_name="profiles", permanent=False)),
    path("people/", RedirectView.as_view(pattern_name="profiles", permanent=False)),
]
