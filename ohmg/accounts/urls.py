from django.urls import include, path

from .views import OHMGSignupView, ProfileView

urlpatterns = [
    ## overwrite the default allauth signup view here
    path("account/signup/", OHMGSignupView.as_view(), name="account_signup"),
    path("account/", include("allauth.urls")),
    path("profile/<str:username>/", ProfileView.as_view(), name="profile_detail"),
    # path("contributors/", ContributorsView.as_view(), name="contributors"),
]
