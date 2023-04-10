from django.views.generic import TemplateView, RedirectView
from django.urls import path

from .views import (
    SimpleAPI,
    VolumeDetail,
    VolumeTrim,
    HomePage,
    MRMEndpointList,
    MRMEndpointLayer,
    Browse,
)

urlpatterns = [

    path('', HomePage.as_view(), name='home'),
    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
    path('getting-started/', TemplateView.as_view(template_name='getting-started.html'),
        name='getting_started'),
    path('help/', RedirectView.as_view(url="https://about.oldinsurancemaps.net")),
    path('developer/', RedirectView.as_view(url="https://about.oldinsurancemaps.net")),

    path('browse/', Browse.as_view(), name='browse'),
    path('loc/volumes/', RedirectView.as_view(pattern_name='browse', permanent=True), name='volumes_list'),
    path('loc/api/', SimpleAPI.as_view() , name='lc_api'),
    path('loc/<str:volumeid>/', VolumeDetail.as_view(), name="volume_summary"),
    path('loc/trim/<str:volumeid>/', VolumeTrim.as_view(), name="volume_trim"),
    path('mrm/', MRMEndpointList.as_view(), name="mrm_layer_list"),
    path('mrm/<str:layerid>/', MRMEndpointLayer.as_view(), name="mrm_get_resource"),
]
