from django.conf import settings
from django.contrib.sites.models import Site


def site_info(request):
    """Return site name, build number, etc."""

    site = Site.objects.get_current()
    return {
        "SITE_NAME": site.name,
        "SITE_DOMAIN": site.domain,
        "BUILD_NUMBER": settings.BUILD_NUMBER,
    }
