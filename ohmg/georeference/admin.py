from django.contrib import admin

from ohmg.georeference.models import (
    GCP,
    GCPGroup,
    PrepSession,
    GeorefSession,
    LayerSet,
    LayerSetCategory,
    SessionLock,
)


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


# class ItemBaseAdmin(admin.ModelAdmin):
#     raw_id_fields = ("vrs",)


# admin.site.register(ItemBase, ItemBaseAdmin)


class GCPAdmin(admin.ModelAdmin):
    readonly_fields = ("last_modified",)
    list_display = ("id", "gcp_group")


admin.site.register(GCP, GCPAdmin)
admin.site.register(GCPGroup)


class SessionAdmin(admin.ModelAdmin):
    raw_id_fields = ("doc2", "reg2", "lyr2")
    readonly_fields = ("date_created", "date_modified", "date_run")
    list_display = [
        "__str__",
        "user",
        "stage",
        "status",
        "note",
        "date_created",
        "date_modified",
        "date_run",
    ]
    list_filter = ("stage",)


class PrepSessionAdmin(SessionAdmin):
    exclude = ("type",)


class GeorefSessionAdmin(SessionAdmin):
    exclude = ("type",)


admin.site.register(PrepSession, PrepSessionAdmin)
admin.site.register(GeorefSession, GeorefSessionAdmin)


# class DocumentAdmin(admin.ModelAdmin):
#     search_fields = ("title", "status")
#     list_display = ("title", "status", "lock_enabled")
#     exclude = ("type", "layer_file", "bbox_polygon")
#     list_filter = ("lock_enabled", "status")
#     raw_id_fields = ("vrs",)


# class LayerAdmin(admin.ModelAdmin):
#     search_fields = ("title", "status")
#     exclude = ("type", "document_file")
#     list_filter = ("lock_enabled",)
#     raw_id_fields = ("vrs",)


# admin.site.register(Document, DocumentAdmin)
# admin.site.register(LayerV1, LayerAdmin)


class SessionLockAdmin(admin.ModelAdmin):
    raw_id_fields = ["session"]


admin.site.register(SessionLock, SessionLockAdmin)

admin.site.register(LayerSetCategory)
