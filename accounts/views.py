from avatar.templatetags.avatar_tags import avatar_url
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views import View
from django.urls import reverse

from .schemas import UserSchema

class ProfileView(View):

    def get(self, request, username):

        u = get_object_or_404(get_user_model(), username=username)

        return render(
            request,
            "accounts/profile.html",
            context={
                "svelte_params": {
                    "CURRENT_USERNAME": request.user.username,
                    "PROFILE_USER": UserSchema.from_orm(u).dict(),
                    "CHANGE_AVATAR_URL": reverse('avatar_change'),
                    "SESSION_API_URL": reverse("api-beta:session_list")
                }
            }
        )


class Participants(View):

    def get(self, request):

        return render(
            request,
            "accounts/participants.html",
            context={
                "svelte_params": {
                    "USER_API_URL": reverse("api-beta:user_list")
                }
            },
        )