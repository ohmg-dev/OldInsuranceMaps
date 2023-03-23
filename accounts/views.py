from django import forms
from django.contrib.auth import authenticate, login
from django.http import HttpResponse
from django.shortcuts import render


class AjaxLoginForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput)
    username = forms.CharField()


def ajax_login(request):
    if request.method != 'POST':
        return HttpResponse(
            content="ajax login requires HTTP POST",
            status=405,
            content_type="text/plain"
        )
    form = AjaxLoginForm(data=request.POST)
    if form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = authenticate(username=username, password=password)
        if user is None or not user.is_active:
            return HttpResponse(
                content="bad credentials or disabled user",
                status=400,
                content_type="text/plain"
            )
        else:
            login(request, user)
            if request.session.test_cookie_worked():
                request.session.delete_test_cookie()
            return HttpResponse(
                content="successful login",
                status=200,
                content_type="text/plain"
            )
    else:
        return HttpResponse(
            "The form you submitted doesn't look like a username/password combo.",
            content_type="text/plain",
            status=400)