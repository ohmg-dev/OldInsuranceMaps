from django.contrib import admin

from ohmg.core.models import MapGroup, Map, Document, Region, Layer, LayerSet, LayerSetCategory


class MapAdmin(admin.ModelAdmin):
    list_filter = ("status", "sponsor", "loaded_by")
    list_display = ("title", "load_date", "loaded_by", "sponsor")
    search_fields = ("title",)
    autocomplete_fields = ("locales",)


class DocumentAdmin(admin.ModelAdmin):
    search_fields = ("title",)
    readonly_fields = ("prepared", "title")
    raw_id_fields = ("map",)


class RegionAdmin(admin.ModelAdmin):
    search_fields = ("title",)
    raw_id_fields = ("document",)
    readonly_fields = ("georeferenced", "title")


class LayerAdmin(admin.ModelAdmin):
    search_fields = ("title",)
    raw_id_fields = ("region", "layerset2")
    readonly_fields = ("title",)


admin.site.register(MapGroup)
admin.site.register(Map, MapAdmin)
admin.site.register(Document, DocumentAdmin)
admin.site.register(Region, RegionAdmin)
admin.site.register(Layer, LayerAdmin)


class LayerSetAdmin(admin.ModelAdmin):
    raw_id_fields = ("map",)
    readonly_fields = (
        "layer_display_list",
        "extent",
        "multimask_extent",
        "multimask",
    )
    search_fields = ("map__title",)
    list_filter = ("category",)


admin.site.register(LayerSet, LayerSetAdmin)
admin.site.register(LayerSetCategory)
