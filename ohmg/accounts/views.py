import requests
from allauth.account.views import SignupView
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, render
from django.views import View

from ohmg.api.schemas import UserSchema
from ohmg.conf.http import (
    generate_ohmg_context,
)


class ProfileView(View):
    def get(self, request, username):
        u = get_object_or_404(get_user_model(), username=username)
        ohmg_context = generate_ohmg_context(request)
        profile_user = UserSchema.from_orm(u).dict()
        return render(
            request,
            "accounts/profile.html",
            context={
                "CONTEXT": ohmg_context,
                "PROFILE_USER": profile_user,
                "SESSIONLIST_PROPS": {
                    "CONTEXT": ohmg_context,
                    "showUser": False,
                    "userFilter": {"id": username, "label": username},
                },
            },
        )


class ContributorsView(View):
    def get(self, request):
        ohmg_context = generate_ohmg_context(request)
        return render(
            request,
            "accounts/contributors.html",
            context={
                "CONTEXT": ohmg_context,
                "CONTRIBUTORS_PROPS": {
                    "CONTEXT": ohmg_context,
                },
            },
        )


def verify_prosopo_token(token: str):
    url = "https://api.prosopo.io/siteverify"
    response = requests.post(url, json={"secret": settings.PROSOPO_SECRET_KEY, "token": token})
    return response.json().get("verified", False)


class OHMGSignupView(SignupView):
    def form_valid(self, form):
        if settings.PROSOPO_SITE_KEY:
            token = form.data.get("captcha_payload")
            ## first check that a payload was sent with the form
            if not token:
                raise ValidationError("Invalid form", code="invalid")
            ## now check the token against prosopo endpoint
            if not verify_prosopo_token(token):
                raise ValidationError("Invalid token", code="invalid")
        return super(self.__class__, self).form_valid(form)
