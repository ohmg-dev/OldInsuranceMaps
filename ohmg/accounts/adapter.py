from django.urls import reverse

from allauth.account.adapter import DefaultAccountAdapter


class AccountAdapter(DefaultAccountAdapter):
    def get_login_redirect_url(self, request):
        return request.POST.get("next", reverse('profile_detail', kwargs={'username': request.user.username}))
