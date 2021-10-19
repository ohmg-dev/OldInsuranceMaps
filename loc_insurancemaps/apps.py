from django.apps import AppConfig as BaseAppConfig

def run_setup_hooks(*args, **kwargs):
    from django.conf import settings
    from .celeryapp import app as celeryapp
    if celeryapp not in settings.INSTALLED_APPS:
        settings.INSTALLED_APPS += (celeryapp, )

class AppConfig(BaseAppConfig):

    name = "loc_insurancemaps"
    verbose_name = "LOC Insurance Maps"

    def ready(self):
        super(AppConfig, self).ready()
        run_setup_hooks()
