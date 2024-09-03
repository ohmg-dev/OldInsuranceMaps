from django.contrib import admin

from ohmg.core.models import (
    MapGroup,
    Map,
    Document,
    Region,
    Layer,
)


class DocumentAdmin(admin.ModelAdmin):
    readonly_fields = ("prepared", "title")


class RegionAdmin(admin.ModelAdmin):
    raw_id_fields = ("document", "gcp_group")
    readonly_fields = ("georeferenced", "title")


class LayerAdmin(admin.ModelAdmin):
    raw_id_fields = ("region", "layerset")
    readonly_fields = ("title",)

admin.site.register(MapGroup)
admin.site.register(Map)
admin.site.register(Document, DocumentAdmin)
admin.site.register(Region, RegionAdmin)
admin.site.register(Layer, LayerAdmin)
