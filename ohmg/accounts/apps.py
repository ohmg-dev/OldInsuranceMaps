from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = "ohmg.accounts"

    def ready(self):
        from . import signals  # noqa: F401
