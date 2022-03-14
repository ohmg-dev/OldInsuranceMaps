__version__ = (0, 0, 1, 'beta', 0)

default_app_config = "georeference.apps.GeoreferenceConfig"

def get_version():
    import georeference.version
    return georeference.version.get_version(__version__)
