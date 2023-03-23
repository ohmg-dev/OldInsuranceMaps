from django.urls import path

from accounts.views import ajax_login

urlpatterns = [
    path('new-login/', ajax_login, name="new_login"),
]