from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views import View


class ProfileView(View):

    def get(self, request, username):

        f = request.GET.get("f", None)
        u = get_object_or_404(get_user_model(), username=username)
        data = u.serialize()

        if f == "json":
            return JsonResponse(data)

        else:
            return render(
                request,
                "accounts/profile.html",
                context={
                    "svelte_params": {
                        "USER": data,
                    }
                }
            )


class Participants(View):

    def get(self, request):

        profiles = get_user_model().objects.all().exclude(username="AnonymousUser").order_by("username")

        data = [i.serialize() for i in profiles]

        return render(
            request,
            "accounts/participants.html",
            context={
                "svelte_params": {
                    "PARTICIPANTS": data,
                }
            },
        )