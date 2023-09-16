from avatar.templatetags.avatar_tags import avatar_url
from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import render, get_object_or_404
from django.views import View
from django.urls import reverse

from ohmg.accounts.schemas import UserSchema
from ohmg.api.models import Key

class ProfileView(View):

    def get(self, request, username):

        u = get_object_or_404(get_user_model(), username=username)

        api_keys = [i for i in Key.objects.filter(account=u).values_list('value', flat=True)]

        return render(
            request,
            "index.html",
            context={
                "params": {
                    "PAGE_NAME": 'profile',
                    "PARAMS": {
                        "CURRENT_USERNAME": request.user.username,
                        "PROFILE_USER": UserSchema.from_orm(u).dict(),
                        "CHANGE_AVATAR_URL": reverse('avatar_change'),
                        "SESSION_API_URL": reverse("api-beta:session_list"),
                        "OHMG_API_KEY": settings.OHMG_API_KEY,
                        "USER_API_KEYS": api_keys,
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
                    "PAGE_NAME": "profiles",
                    "PARAMS": {
                        "OHMG_API_KEY": settings.OHMG_API_KEY,
                        "USER_API_URL": reverse("api-beta:user_list"),
                    }
                }
            },
        )
