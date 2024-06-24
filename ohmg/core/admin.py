from django.contrib import admin

from ohmg.core.models import (
    MapGroup,
    Map,
    Document,
    Region,
)

admin.site.register(MapGroup)
admin.site.register(Map)
admin.site.register(Document)
admin.site.register(Region)
