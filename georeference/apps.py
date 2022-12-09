from django.apps import AppConfig


class GeoreferenceConfig(AppConfig):
    name = 'georeference'

    def ready(self):
        import georeference.receivers
