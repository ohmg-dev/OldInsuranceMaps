from django.urls.converters import StringConverter

from .models import Place


class PlaceConverter(StringConverter):
    def to_python(self, value):
        try:
            # returns the actual object and passes directly to view
            return Place.objects.get(slug=value)
        except Place.DoesNotExist:
            raise ValueError

    def to_url(self, obj):
        ## unclear why this if/else is needed, it should always be an obj but
        ## sometimes the actual slug string is passed in
        if isinstance(obj, str):
            return obj
        else:
            return str(obj.slug)
