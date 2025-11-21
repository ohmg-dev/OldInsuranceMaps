from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserChangeForm, CustomUserCreationForm
from .models import APIKey, User


class LocalUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User
    list_display = ["email", "username", "date_joined", "last_login"]
    ordering = ("-date_joined",)


admin.site.register(User, LocalUserAdmin)


class APIKeyAdmin(admin.ModelAdmin):
    list_display = ("value", "account", "active", "request_count")
    readonly_fields = ("value", "request_count")


admin.site.register(APIKey, APIKeyAdmin)
