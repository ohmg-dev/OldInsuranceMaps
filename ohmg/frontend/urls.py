from django.views.generic import TemplateView, RedirectView
from django.urls import path

from ohmg.frontend.views import (
    VolumeDetail,
    VolumeTrim,
    HomePage,
    MRMEndpointList,
    MRMEndpointLayer,
    Browse,
    BasicPage,
)

urlpatterns = [
    path('', HomePage.as_view(), name='home'),
    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
    path('about/', BasicPage.as_view(), name='about', kwargs={
        "slug":"about",
        "title":"About",
    }),
    path('about-sanborn-maps/', BasicPage.as_view(), name='about-sanborn-maps', kwargs={
        "slug":"about-sanborn-maps",
        "title":"About Sanborn Maps",
    }),
    path('faq/', BasicPage.as_view(), name='faq', kwargs={
        "slug":"faq",
        "title":"FAQ",
    }),
    path('contact/', BasicPage.as_view(), name='contact', kwargs={
        "slug":"contact",
        "title":"Contact",
    }),
    # path('getting-started/', BasicPage.as_view(), name='faq', kwargs={"page_name":"getting-started"}),
    path('activity/', BasicPage.as_view(), name='activity', kwargs={
        "slug":"activity",
        "title": "Activity",
    }),
    path('search/', Browse.as_view(), name='search'),
    path('browse/', RedirectView.as_view(pattern_name='search'), name='browse'),
    path('loc/volumes/', RedirectView.as_view(pattern_name='search', permanent=True), name='volumes_list'),
    path('loc/<str:volumeid>/', VolumeDetail.as_view(), name="volume_summary"),
    path('mrm/', MRMEndpointList.as_view(), name="mrm_layer_list"),
    path('mrm/<str:layerid>/', MRMEndpointLayer.as_view(), name="mrm_get_resource"),
]
