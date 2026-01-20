from django.apps import AppConfig


class GeoreferenceConfig(AppConfig):
    name = "ohmg.georeference"

    def ready(self):
        from . import signals  # noqa: F401
