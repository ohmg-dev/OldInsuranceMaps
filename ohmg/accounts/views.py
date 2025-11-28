import json

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, render
from django.views import View

from ohmg.api.schemas import UserSchema
from ohmg.conf.http import (
    JsonResponseBadRequest,
    JsonResponseFail,
    JsonResponseSuccess,
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
                "CONTRIBUTORLIST_PROPS": {
                    "CONTEXT": ohmg_context,
                    # "showUser": False,
                    # "userFilter": {"id": username, "label": username},
                },
            },
        )


def verify_prosopo_token(request):
    if request.method == "POST":
        if request.body:
            body = json.loads(request.body)
            token = body.get("token")
            url = "https://api.prosopo.io/siteverify"
            response = requests.post(
                url, json={"secret": settings.PROSOPO_SECRET_KEY, "token": token}
            )
            success = response.json().get("verified", False)
            return JsonResponseSuccess() if success else JsonResponseFail()
        else:
            return JsonResponseBadRequest()
    else:
        raise JsonResponseBadRequest()
