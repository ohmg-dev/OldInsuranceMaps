from django.urls import include, path

from .views import APIKeysView, OHMGSignupView, ProfilesView, ProfileView

urlpatterns = [
    ## overwrite the default allauth signup view here
    path("account/signup/", OHMGSignupView.as_view(), name="account_signup"),
    path("account/api-keys/", APIKeysView.as_view(), name="api_keys"),
    path("account/", include("allauth.urls")),
    path("profile/<str:username>/", ProfileView.as_view(), name="profile_detail"),
    path("profiles/", ProfilesView.as_view(), name="profiles"),
]
