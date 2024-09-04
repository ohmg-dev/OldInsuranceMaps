from django.contrib.auth import get_user_model
from django.shortcuts import render, get_object_or_404
from django.views import View

from ohmg.core.context_processors import generate_ohmg_context
from ohmg.core.api.schemas import UserSchema

class ProfileView(View):

    def get(self, request, username):

        u = get_object_or_404(get_user_model(), username=username)

        return render(
            request,
            "index.html",
            context={
                "params": {
                    "CONTEXT": generate_ohmg_context(request),
                    "PAGE_NAME": 'profile',
                    "PARAMS": {
                        "PROFILE_USER": UserSchema.from_orm(u).dict(),
                    }
                }
            }
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
