from django.apps import AppConfig as BaseAppConfig

class AppConfig(BaseAppConfig):

    name = "loc_insurancemaps"
    verbose_name = "LOC Insurance Maps"

    def ready(self):
        super(AppConfig, self).ready()
