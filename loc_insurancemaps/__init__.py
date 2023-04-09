from .celeryapp import app as celery_app

__all__ = ('celery_app',)

__version__ = (0, 1, 0, 'beta', 0)


default_app_config = "loc_insurancemaps.apps.AppConfig"


def get_version():
    import loc_insurancemaps.version
    return loc_insurancemaps.version.get_version(__version__)
