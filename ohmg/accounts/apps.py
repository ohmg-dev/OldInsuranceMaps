from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = "ohmg.accounts"

    def ready(self):
        import ohmg.accounts.receivers  # noqa: F401
