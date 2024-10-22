from django.urls import path, register_converter
from django.urls.converters import StringConverter
from django.views.generic import RedirectView

from .views import (
    PageView,
    MapSummary,
    ResourceSummary,
)

from .models import Page

class PageConverter(StringConverter):

    def to_python(self, value):
        try:
            # returns the actual object and passes directly to view
            return Page.objects.get(slug=value, published=True)
        except Page.DoesNotExist:
            raise ValueError

    def to_url(self, obj):
        return str(obj.slug)

register_converter(PageConverter, 'page-slug')

urlpatterns = [
    # APPEND_SLASH would handle this, but I believe it is applied AFTER url matching
    # (without this redirect bare page urls were returning 404)
    path('<page-slug:page>', RedirectView.as_view(pattern_name="page-view", permanent=True)),
    path('<page-slug:page>/', PageView.as_view(), name="page-view"),
    path('map/<str:identifier>', MapSummary.as_view(), name="map_summary"),
    path('document/<int:pk>', ResourceSummary.as_view(), kwargs={"resource_type":"document"}, name="document_detail"),
    path('region/<int:pk>', ResourceSummary.as_view(), kwargs={"resource_type":"region"}, name="region_detail"),
    path('layer/<int:pk>', ResourceSummary.as_view(), kwargs={"resource_type":"layer"}, name="layer_detail"),
    # temporary overlap here, ultimately will remove all /loc/ and /item/ urls
    path('item/<str:identifier>', RedirectView.as_view(pattern_name='map_summary', permanent=True), name="volume_summary"),
    path('loc/volumes/', RedirectView.as_view(pattern_name='search', permanent=True), name='volumes_list'),
    path('loc/<str:identifier>/', RedirectView.as_view(pattern_name='map_summary', permanent=True), name="volume_summary"),
]
