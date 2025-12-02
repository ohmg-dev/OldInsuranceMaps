from django.contrib import admin

from ohmg.core.models import (
    Document,
    Layer,
    LayerSet,
    LayerSetCategory,
    Map,
    MapGroup,
    Region,
    RegionCategory,
)


class MapAdmin(admin.ModelAdmin):
    list_filter = ("sponsor", "loaded_by")
    list_display = ("title", "load_date", "loaded_by", "sponsor")
    search_fields = ("title",)
    autocomplete_fields = ("locales",)
    readonly_fields = (
        "document_ct",
        "unprepared_ct",
        "region_ct",
        "prepared_ct",
        "layer_ct",
        "skip_ct",
        "nonmap_ct",
        "completion_pct",
        "multimask_ct",
        "multimask_rank",
    )


class DocumentAdmin(admin.ModelAdmin):
    search_fields = ("title",)
    readonly_fields = ("prepared", "title")
    raw_id_fields = ("map",)


class RegionAdmin(admin.ModelAdmin):
    search_fields = ("title",)
    raw_id_fields = ("document",)
    readonly_fields = ("georeferenced", "title")
    list_display = ("title", "category", "georeferenced")
    list_filter = ("category",)


class LayerAdmin(admin.ModelAdmin):
    search_fields = ("title",)
    raw_id_fields = ("region", "layerset2")
    readonly_fields = ("title",)


admin.site.register(MapGroup)
admin.site.register(Map, MapAdmin)
admin.site.register(Document, DocumentAdmin)
admin.site.register(Region, RegionAdmin)
admin.site.register(RegionCategory)
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
