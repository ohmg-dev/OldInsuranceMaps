from django.urls.converters import StringConverter

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
