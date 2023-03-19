from django.conf import settings
from django.urls import path
from django.conf.urls import url, include
from django.views.generic import TemplateView, RedirectView

from geonode.urls import urlpatterns

from .views import (
    SimpleAPI,
    VolumeDetail,
    VolumeTrim,
    HomePage,
    MRMEndpointList,
    MRMEndpointLayer,
    Viewer,
    Browse,
    Participants,
    PlaceLookup,
    PlaceView,
)

if settings.ENABLE_NEWSLETTER:
    urlpatterns += [path('newsletter/', include('newsletter.urls'))]

if 'georeference' in settings.INSTALLED_APPS:
    urlpatterns += [url(r'^', include('georeference.urls'))]

urlpatterns += [
    path('place-lookup/<str:place_slug>', PlaceLookup.as_view(), name='place_lookup_view'),
    path('viewer/', RedirectView.as_view(pattern_name='browse', permanent=False), name='viewer_base'),
    path('viewer/<str:place_slug>/', Viewer.as_view(), name='viewer'),
    path('browse/', Browse.as_view(), name='browse'),
    path('loc/volumes/', RedirectView.as_view(pattern_name='browse', permanent=True), name='volumes_list'),
    path('loc/api/', SimpleAPI.as_view() , name='lc_api'),
    path('loc/<str:volumeid>/', VolumeDetail.as_view(), name="volume_summary"),
    path('loc/trim/<str:volumeid>/', VolumeTrim.as_view(), name="volume_trim"),
    path('mrm/', MRMEndpointList.as_view(), name="mrm_layer_list"),
    path('mrm/<str:layerid>/', MRMEndpointLayer.as_view(), name="mrm_get_resource"),
    path('participants/', Participants.as_view(), name="participants"),
    path('participation/', RedirectView.as_view(pattern_name='participants', permanent=False)),
    # path('<str:place_slug>/view/', Viewer.as_view(), name='place_viewer'),
    path('<str:place_slug>/', PlaceView.as_view(), name='place'),
]

## these url patterns overwrite existing geonode patterns
urlpatterns = [
    url(r'^/?$', HomePage.as_view(), name='home'),
    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
    path('getting-started/', TemplateView.as_view(template_name='getting-started.html'),
        name='getting_started'),
    path('help/', RedirectView.as_view(url="https://about.oldinsurancemaps.net")),
    # path('about/', RedirectView.as_view(url="https://docs.oldinsurancemaps.net")),
    path('developer/', RedirectView.as_view(url="https://about.oldinsurancemaps.net")),
    path('people/', RedirectView.as_view(url="/participants")),
 ] + urlpatterns

if settings.DEBUG:
    urlpatterns += [path('__debug__/', include('debug_toolbar.urls'))]
 