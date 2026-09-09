from django.contrib import admin
from django.utils.safestring import mark_safe

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
    list_filter = ("sponsor", "loaded_by", "access_level")
    list_display = ("title", "load_date", "loaded_by", "access_level", "get_locale")
    search_fields = ("title",)
    autocomplete_fields = ("locales",)
    readonly_fields = (
        "document_ct",
        "unprepared_ct",
        "region_ct",
        "prepared_ct",
        "layer_ct",
        "main_layer_ct",
        "skip_ct",
        "nonmap_ct",
        "completion_pct",
        "multimask_ct",
        "multimask_rank",
    )


class DocumentAdmin(admin.ModelAdmin):
    list_filter = ("prepared", "map")
    list_display = ("title", "page_number", "load_date", "prepared", "map_link")
    search_fields = ("title",)
    readonly_fields = ("prepared", "title")
    raw_id_fields = ("map",)

    @admin.display(description="Map")
    def map_link(self, obj):
        return mark_safe(f'<a href="/admin/core/map/{obj.map.pk}">{obj.map.title}</a>')


class RegionAdmin(admin.ModelAdmin):
    search_fields = ("title",)
    raw_id_fields = ("document",)
    readonly_fields = ("georeferenced", "title")
    list_display = ("title", "category", "georeferenced", "document_link", "map_link")
    list_filter = ("category",)
    # list_display_links = ('title', 'document'

    @admin.display(description="Map")
    def map_link(self, obj):
        return mark_safe(f'<a href="/admin/core/map/{obj.map.pk}">{obj.map.title}</a>')

    @admin.display(description="Document")
    def document_link(self, obj):
        return mark_safe(
            f'<a href="/admin/core/document/{obj.document.pk}">{obj.document.title}</a>'
        )


class LayerAdmin(admin.ModelAdmin):
    search_fields = ("title",)
    raw_id_fields = ("region", "layerset2")
    readonly_fields = ("title",)
    list_display = ("title", "created_by", "region_link", "map_link", "layerset_link")
    list_filter = ("layerset2",)

    @admin.display(description="Map")
    def map_link(self, obj):
        return mark_safe(f'<a href="/admin/core/map/{obj.map.pk}">{obj.map.title}</a>')

    @admin.display(description="Region")
    def region_link(self, obj):
        return mark_safe(f'<a href="/admin/core/region/{obj.region.pk}">{obj.region.title}</a>')

    @admin.display(description="Layerset")
    def layerset_link(self, obj):
        return mark_safe(
            f'<a href="/admin/core/layerset/{obj.layerset2.pk}">{obj.layerset2.category}</a>'
        )


admin.site.register(MapGroup)
admin.site.register(Map, MapAdmin)
admin.site.register(Document, DocumentAdmin)
admin.site.register(Region, RegionAdmin)
admin.site.register(RegionCategory)
admin.site.register(Layer, LayerAdmin)


class LayerSetAdmin(admin.ModelAdmin):
    list_display = (
        "map",
        "category",
        "multimask_date",
    )
    raw_id_fields = ("map",)
    readonly_fields = (
        "layer_display_list",
        "extent",
        "multimask_extent",
        "xyz_tiles_url",
        "multimask_date",
    )
    search_fields = ("map__title",)
    list_filter = ("category",)


admin.site.register(LayerSet, LayerSetAdmin)
admin.site.register(LayerSetCategory)
