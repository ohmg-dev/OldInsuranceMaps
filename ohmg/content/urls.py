from django.conf import settings

from django.urls import path, register_converter
from django.views.generic import RedirectView

from .converters import PageConverter
from .views import (
    HomePage,
    PageView,
    ActivityView,
    Browse,
)

register_converter(PageConverter, "page-slug")

urlpatterns = [
    path("", HomePage.as_view(), name="home"),
    path("activity/", ActivityView.as_view(), name="activity"),
    path("search/", Browse.as_view(), name="search"),
    path("browse/", RedirectView.as_view(pattern_name="search"), name="browse"),
    path("<page-slug:page>/", PageView.as_view(), name="page-view"),
]

if settings.ENABLE_NEWSLETTER:
    from .views import NewsList, NewsArticle

    urlpatterns += [
        path("news/", NewsList.as_view(), name="news"),
        path("news/<str:slug>/", NewsArticle.as_view(), name="article"),
    ]
