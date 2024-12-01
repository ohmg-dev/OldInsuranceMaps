from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from ohmg.core.models import Map


class MapsSitemap(Sitemap):
    priority = 0.5
    changefreq = "monthly"

    def items(self):
        return Map.objects.all().order_by("title")

    def lastmod(self, obj):
        return obj.load_date


class StaticViewSitemap(Sitemap):
    def items(self):
        return [
            "home",
            "activity",
        ]

    def location(self, item):
        return reverse(item)

    def priority(self, item):
        return {"home": 1.0, "activity": 0.8}[item]

    def changefreq(self, item):
        return {"home": "monthly", "activity": "daily"}[item]


sitemaps = {
    "static": StaticViewSitemap,
    "maps": MapsSitemap,
}
