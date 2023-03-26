from django.urls import path
from django.views.generic import RedirectView

from .views import (
    ProfileView,
    Participants,
)

urlpatterns = [
    path('profile/<str:username>/', ProfileView.as_view(), name="profile_detail"),
    path('participants/', Participants.as_view(), name="participants"),
    path('participation/', RedirectView.as_view(pattern_name='participants', permanent=False)),
]