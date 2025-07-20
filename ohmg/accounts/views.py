from django.contrib.auth import get_user_model
from django.shortcuts import render, get_object_or_404
from django.views import View

from ohmg.core.api.schemas import UserSchema
from ohmg.core.http import generate_ohmg_context
from ohmg.core.models import Map


class ProfileView(View):
    def get(self, request, username):
        u = get_object_or_404(get_user_model(), username=username)
        all_maps = Map.objects.exclude(hidden=True).order_by("title")
        filter_list = [
            {"title": i[0], "id": i[1]} for i in all_maps.values_list("title", "identifier")
        ]
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
                    "mapFilterItems": filter_list,
                    "showUser": False,
                    "userFilter": {"id": username},
                },
            },
        )
