from django.conf import settings
from django.urls import path
from django.conf.urls import url, include
from django.views.generic import TemplateView, RedirectView

from geonode.urls import urlpatterns
from geonode.monitoring import register_url_event

from .views import (
    SimpleAPI,
    VolumeDetail,
    VolumeTrim,
    HomePage,
    MRMEndpointList,
    MRMEndpointLayer,
    Viewer,
    Browse,
)

urlpatterns += [
    # path('place/<str:place_slug>', PlaceView.as_view(), name='place_view'),
    path('viewer/', Viewer.as_view(), name='viewer'),
    path('browse/', Browse.as_view(), name='browse'),
    path('loc/volumes/', RedirectView.as_view(pattern_name='browse', permanent=True), name='volumes_list'),
    path('loc/api/', SimpleAPI.as_view() , name='lc_api'),
    path('loc/<str:volumeid>/', VolumeDetail.as_view(), name="volume_summary"),
    path('loc/trim/<str:volumeid>/', VolumeTrim.as_view(), name="volume_trim"),
    path('mrm/', MRMEndpointList.as_view(), name="mrm_layer_list"),
    path('mrm/<str:layerid>/', MRMEndpointLayer.as_view(), name="mrm_get_resource"),
]

if 'georeference' in settings.INSTALLED_APPS:
    urlpatterns += [url(r'^', include('georeference.urls'))]

homepage = register_url_event()(HomePage.as_view())

## these url patterns overwrite existing geonode patterns
urlpatterns = [
    url(r'^/?$', homepage, name='home'),
    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
    path('getting-started/', TemplateView.as_view(template_name='getting-started.html'),
        name='getting_started'),
    path('help/', RedirectView.as_view(url="https://docs.oldinsurancemaps.net")),
    # path('about/', RedirectView.as_view(url="https://docs.oldinsurancemaps.net")),
    path('developer/', RedirectView.as_view(url="https://docs.oldinsurancemaps.net")),
 ] + urlpatterns
 