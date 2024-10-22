from django.conf import settings
from django.views.generic import TemplateView, RedirectView
from django.views.defaults import page_not_found, server_error
from django.urls import path

from ohmg.frontend.views import (
    HomePage,
    MRMEndpointList,
    MRMEndpointLayer,
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
    path('activity/', ActivityView.as_view(), name='activity'),
    path('search/', Browse.as_view(), name='search'),
    path('browse/', RedirectView.as_view(pattern_name='search'), name='browse'),
    path('mrm/', MRMEndpointList.as_view(), name="mrm_layer_list"),
    path('mrm/<str:layerid>/', MRMEndpointLayer.as_view(), name="mrm_get_resource"),
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
