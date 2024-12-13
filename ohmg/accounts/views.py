from django.contrib.auth import get_user_model
from django.shortcuts import render, get_object_or_404
from django.views import View

from ohmg.core.http import generate_ohmg_context
from ohmg.core.api.schemas import UserSchema
from ohmg.core.models import Map


class ProfileView(View):
    def get(self, request, username):
        u = get_object_or_404(get_user_model(), username=username)
        all_maps = Map.objects.exclude(hidden=True).order_by("title")
        filter_list = [
            {"title": i[0], "id": i[1]} for i in all_maps.values_list("title", "identifier")
        ]

        return render(
            request,
            "index.html",
            context={
                "params": {
                    "CONTEXT": generate_ohmg_context(request),
                    "PAGE_NAME": "profile",
                    "PARAMS": {
                        "PROFILE_USER": UserSchema.from_orm(u).dict(),
                        "MAP_FILTER_LIST": filter_list,
                    },
                }
            },
        )


class Participants(View):
    def get(self, request):
        return render(
            request,
            "index.html",
            context={
                "params": {
                    "CONTEXT": generate_ohmg_context(request),
                    "PAGE_NAME": "profiles",
                }
            },
        )
