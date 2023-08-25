from django.apps import AppConfig


class GeoreferenceConfig(AppConfig):
    name = 'ohmg.georeference'

    def ready(self):
        import ohmg.georeference.receivers
