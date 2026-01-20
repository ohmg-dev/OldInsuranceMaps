from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserChangeForm, CustomUserCreationForm
from .models import APIKey, User


class LocalUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User
    list_display = ["email", "username", "date_joined", "last_login", "added_to_newsletter"]
    ordering = ("-date_joined",)

    ## reference: https://stackoverflow.com/a/15013810
    fieldsets = UserAdmin.fieldsets + ((None, {"fields": ("added_to_newsletter",)}),)


admin.site.register(User, LocalUserAdmin)


class APIKeyAdmin(admin.ModelAdmin):
    list_display = ("value", "account", "active", "request_count")
    readonly_fields = ("value", "request_count")


admin.site.register(APIKey, APIKeyAdmin)
