from django.conf import settings
from django.urls import path
from django.contrib import admin
from django.conf.urls import url, include
from django.views.generic import TemplateView, RedirectView

# from geonode.urls import urlpatterns

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
    PlaceView,
)


urlpatterns = [
    path('admin/', admin.site.urls, name="admin"),
    path('account/', include("allauth.urls")),
]
# urlpatterns = []

if settings.ENABLE_NEWSLETTER:
    urlpatterns += [path('newsletter/', include('newsletter.urls'))]

if 'georeference' in settings.INSTALLED_APPS:
    urlpatterns += [url(r'^', include('georeference.urls'))]

urlpatterns += [
    path('browse/', Browse.as_view(), name='browse'),
    path('loc/volumes/', RedirectView.as_view(pattern_name='browse', permanent=True), name='volumes_list'),
    path('loc/api/', SimpleAPI.as_view() , name='lc_api'),
    path('loc/<str:volumeid>/', VolumeDetail.as_view(), name="volume_summary"),
    path('loc/trim/<str:volumeid>/', VolumeTrim.as_view(), name="volume_trim"),
    path('mrm/', MRMEndpointList.as_view(), name="mrm_layer_list"),
    path('mrm/<str:layerid>/', MRMEndpointLayer.as_view(), name="mrm_get_resource"),
    path('participants/', Participants.as_view(), name="participants"),
    path('participation/', RedirectView.as_view(pattern_name='participants', permanent=False)),
    path('profile/<str:username>/', HomePage.as_view(), name="profile_detail"),
]

urlpatterns += [path('', include('places.urls'))]
# urlpatterns += [path('', include('accounts.urls'))]

## these url patterns overwrite existing geonode patterns
urlpatterns = [
    path('', HomePage.as_view(), name='home'),
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
 