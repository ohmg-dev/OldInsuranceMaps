from django.views.generic import TemplateView, RedirectView
from django.urls import path

# temporary overlap here, ultimately will remove the /loc/ url
from ohmg.content.views import ItemView
from ohmg.frontend.views import (
    VolumeTrim,
    HomePage,
    MRMEndpointList,
    MRMEndpointLayer,
    Browse,
    ActivityView,
    NewsList,
    NewsArticle,
    MarkdownPage,
    Viewer,
)

urlpatterns = [
    path('', HomePage.as_view(), name='home'),
    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
    path('about-sanborn-maps/', MarkdownPage.as_view(), {"slug":"about-sanborn-maps"}),
    path('about/', MarkdownPage.as_view(), {"slug":"about"}),
    path('contact/', MarkdownPage.as_view(), {"slug":"contact"}),
    path('faq/', MarkdownPage.as_view(), {"slug":"faq"}),
    path('getting-started/', MarkdownPage.as_view(), {"slug":"getting-started"}),
    path('activity/', ActivityView.as_view(), name='activity'),
    path('search/', Browse.as_view(), name='search'),
    path('browse/', RedirectView.as_view(pattern_name='search'), name='browse'),
    path('loc/volumes/', RedirectView.as_view(pattern_name='search', permanent=True), name='volumes_list'),
    # temporary overlap here, ultimately will remove the /loc/ url
    path('loc/<str:volumeid>/', ItemView.as_view(), name="volume_summary"),
    path('loc/trim/<str:volumeid>/', VolumeTrim.as_view(), name="volume_trim"),
    path('mrm/', MRMEndpointList.as_view(), name="mrm_layer_list"),
    path('mrm/<str:layerid>/', MRMEndpointLayer.as_view(), name="mrm_get_resource"),
    path('news/', NewsList.as_view(), name="news"),
    path('news/<str:slug>/', NewsArticle.as_view(), name="article"),
    path('viewer/', RedirectView.as_view(pattern_name='browse', permanent=False), name='viewer_base'),
    path('viewer/<str:place_slug>/', Viewer.as_view(), name='viewer'),
]
