from django.contrib.auth import get_user_model
from django.shortcuts import render, get_object_or_404
from django.views import View

from ohmg.api.schemas import UserSchema
from ohmg.conf.http import generate_ohmg_context


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
                "PAGE_TITLE": username,
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
