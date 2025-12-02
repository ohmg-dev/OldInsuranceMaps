from allauth.account.adapter import DefaultAccountAdapter
from django.urls import reverse


class AccountAdapter(DefaultAccountAdapter):
    def get_login_redirect_url(self, request):
        return request.POST.get(
            "next",
            reverse("profile_detail", kwargs={"username": request.user.username}),
        )
