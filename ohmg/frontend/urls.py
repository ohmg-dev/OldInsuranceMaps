from django.conf import settings
from django.contrib.sitemaps.views import sitemap
from django.urls import path, register_converter
from django.views.generic import RedirectView, TemplateView

from .converters import PageConverter

# from .models import Redirect
from .sitemap import sitemaps
from .views import (
    ActivityView,
    Browse,
    HomePage,
    PageView,
)

register_converter(PageConverter, "page-slug")

urlpatterns = [
    ## app urls paths
    path("", HomePage.as_view(), name="home"),
    path("activity/", ActivityView.as_view(), name="activity"),
    path("search/", Browse.as_view(), name="search"),
    path("<page-slug:page>/", PageView.as_view(), name="page-view"),
    ## conventional url paths
    path(
        "robots.txt",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
    ),
    path(
        "favicon.ico",
        RedirectView.as_view(url=settings.STATIC_URL + "favicon.ico", permanent=True),
    ),
    path(
        "sitemap.xml/",
        sitemap,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),
]
