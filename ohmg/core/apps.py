from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ohmg.core"

    def ready(self):
        import ohmg.core.receivers  # noqa: F401
