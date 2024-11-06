from django.conf import settings
from django.views.generic import TemplateView, RedirectView
from django.views.defaults import page_not_found, server_error
from django.urls import path

from ohmg.core.views import (
    MapView,
    DocumentView,
    RegionView,
    LayerView,
)
from ohmg.frontend.views import (
    HomePage,
    Browse,
    ActivityView,
    Viewer,
)

def debug_page_not_found(request):
    return page_not_found(request, None)

# this one doesn't work yet
def debug_server_error(request):
    return server_error(request)

urlpatterns = [
    path('', HomePage.as_view(), name='home'),
    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
    path('favicon.ico', RedirectView.as_view(url=settings.STATIC_URL + "favicon.ico", permanent=True)),

    path('map/<str:identifier>', MapView.as_view(), name="map_summary"),
    path('document/<int:pk>', DocumentView.as_view(), name="document_view"),
    path('region/<int:pk>', RegionView.as_view(), name="region_view"),
    path('layer/<int:pk>', LayerView.as_view(), name="layer_view"),
    # temporary overlap here, ultimately will remove all /loc/ and /item/ urls
    path('item/<str:identifier>', RedirectView.as_view(pattern_name='map_summary', permanent=True), name="volume_summary"),
    path('loc/volumes/', RedirectView.as_view(pattern_name='search', permanent=True), name='volumes_list'),
    path('loc/<str:identifier>/', RedirectView.as_view(pattern_name='map_summary', permanent=True), name="volume_summary"),

    path('activity/', ActivityView.as_view(), name='activity'),
    path('search/', Browse.as_view(), name='search'),
    path('browse/', RedirectView.as_view(pattern_name='search'), name='browse'),
    path('viewer/', RedirectView.as_view(pattern_name='browse', permanent=False), name='viewer_base'),
    path('viewer/<str:place_slug>/', Viewer.as_view(), name='viewer'),
]

if settings.ENABLE_NEWSLETTER:
    from ohmg.frontend.views import NewsList, NewsArticle
    urlpatterns += [
        path('news/', NewsList.as_view(), name="news"),
        path('news/<str:slug>/', NewsArticle.as_view(), name="article"),
    ]

if settings.DEBUG:
    urlpatterns += [
        path("404/", debug_page_not_found),
        path("500/", debug_server_error),
    ]
