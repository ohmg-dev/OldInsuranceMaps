from django.conf import settings
from django.contrib.sites.models import Site


def site_info(request):
    """Return site name, build number, etc."""

    site = Site.objects.get_current()
    return {
        "SITE_NAME": site.name,
        "SITE_DOMAIN": site.domain,
        "BUILD_NUMBER": settings.BUILD_NUMBER,
        "PLAUSIBLE_DATA_DOMAIN": settings.PLAUSIBLE_DATA_DOMAIN,
        "PLAUSIBLE_SOURCE_SCRIPT": settings.PLAUSIBLE_SOURCE_SCRIPT,
    }
