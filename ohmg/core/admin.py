from django.contrib import admin

from ohmg.core.models import (
    MapGroup,
    Map,
    Document,
    Region,
    Layer,
)

class RegionAdmin(admin.ModelAdmin):
    raw_id_fields = ("document",)

class LayerAdmin(admin.ModelAdmin):
    raw_id_fields = ("region", "layerset")

admin.site.register(MapGroup)
admin.site.register(Map)
admin.site.register(Document)
admin.site.register(Region, RegionAdmin)
admin.site.register(Layer, LayerAdmin)
