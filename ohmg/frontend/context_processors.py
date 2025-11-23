from django.conf import settings
from django.contrib.sites.models import Site

from .models import Navbar


def site_info(request):
    """Return site name, build number, etc."""

    navbars = Navbar.objects.all()
    navbar_config = {"image_url": "", "items": []}
    if navbars.count() > 0:
        nav = navbars[0]
        navbar_config["image_url"] = nav.image_url
        navbar_config["left_side"] = nav.left_side

        ## create a list of url prefixes that will be used to determine if the
        ## top-level item should be active (this drives CSS styling)
        if "items" in navbar_config["left_side"]:
            for item in navbar_config["left_side"]["items"]:
                item["active_routes"] = []
                if "extra_active_routes" in item:
                    item["active_routes"] += item.pop("extra_active_routes")
                if "link" in item:
                    item["active_routes"].append(item["link"].lstrip("/").rstrip("/"))
                if "children" in item:
                    for child in item["children"]:
                        if "link" in child:
                            item["active_routes"].append(child["link"].lstrip("/").rstrip("/"))

    site = Site.objects.get_current()
    return {
        "SITE_NAME": site.name,
        "SITE_DOMAIN": site.domain,
        "NAVBAR_CONFIG": navbar_config,
        "BUILD_NUMBER": settings.BUILD_NUMBER,
        "CURRENT_ROUTE": request.path.split("/")[1],
        "PLAUSIBLE_DATA_DOMAIN": settings.PLAUSIBLE_DATA_DOMAIN,
        "PLAUSIBLE_SOURCE_SCRIPT": settings.PLAUSIBLE_SOURCE_SCRIPT,
        "PROSOPO_SITE_KEY": settings.PROSOPO_SITE_KEY,
    }
