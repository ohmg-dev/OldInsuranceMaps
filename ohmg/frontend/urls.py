from django.conf import settings
from django.contrib.sitemaps.views import sitemap
from django.urls import path, register_converter
from django.views.generic import RedirectView, TemplateView

from .converters import PageConverter
from .sitemap import sitemaps
from .views import (
    HomePage,
    PageView,
    ActivityView,
    Browse,
    Participants,
)

register_converter(PageConverter, "page-slug")

urlpatterns = [
    ## app urls paths
    path("", HomePage.as_view(), name="home"),
    path("activity/", ActivityView.as_view(), name="activity"),
    path("search/", Browse.as_view(), name="search"),
    path("profiles/", Participants.as_view(), name="profiles"),
    path("<page-slug:page>/", PageView.as_view(), name="page-view"),
    # make sure old links go to the proper page, use permanent=False for now...
    path("browse/", RedirectView.as_view(pattern_name="search"), name="browse"),
    path("participants/", RedirectView.as_view(pattern_name="profiles", permanent=False)),
    path("participation/", RedirectView.as_view(pattern_name="profiles", permanent=False)),
    path("people/", RedirectView.as_view(pattern_name="profiles", permanent=False)),
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

if settings.ENABLE_NEWSLETTER:
    from .views import NewsList, NewsArticle

    urlpatterns += [
        path("news/", NewsList.as_view(), name="news"),
        path("news/<str:slug>/", NewsArticle.as_view(), name="article"),
    ]
