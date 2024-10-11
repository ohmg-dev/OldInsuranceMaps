from django.contrib import admin

from ohmg.georeference.models import (
    GCP,
    GCPGroup,
    LayerV1,
    Document,
    DocumentLink,
    PrepSession,
    GeorefSession,
    ItemBase,
    LayerSet,
    SessionLock,
)

class LayerSetAdmin(admin.ModelAdmin):
    raw_id_fields = ("map", "volume")
    readonly_fields = (
        'annotation_display_list',
        'layer_display_list',
        'extent',
        'multimask_extent',
        'multimask',
    )
    search_fields = ('volume__city',)

admin.site.register(LayerSet, LayerSetAdmin)

class ItemBaseAdmin(admin.ModelAdmin):
    raw_id_fields = ("vrs",)

admin.site.register(ItemBase, ItemBaseAdmin)

class GCPAdmin(admin.ModelAdmin):
    readonly_fields = ('last_modified',)
    list_display = ('id', 'gcp_group')

admin.site.register(GCP, GCPAdmin)
admin.site.register(GCPGroup)

class SessionAdmin(admin.ModelAdmin):
    raw_id_fields = ("doc", "lyr", "doc2", "reg2", "lyr2")
    readonly_fields = ('date_created', 'date_modified', 'date_run')
    list_display = ['__str__', 'doc', 'lyr', 'user', 'stage', 'status', 'note', 'date_created', 'date_modified', 'date_run']
    list_filter = ('stage', )

class PrepSessionAdmin(SessionAdmin):
    exclude = ('type', 'layer')
    list_display = [i for i in SessionAdmin.list_display if i != "layer"]

class GeorefSessionAdmin(SessionAdmin):
    exclude = ('type', )

class TrimSessionAdmin(SessionAdmin):
    exclude = ('type', 'document')
    list_display = [i for i in SessionAdmin.list_display if i != "document"]

admin.site.register(PrepSession, PrepSessionAdmin)
admin.site.register(GeorefSession, GeorefSessionAdmin)

class DocumentAdmin(admin.ModelAdmin):
    search_fields = ('title', 'status')
    list_display = ('title', 'status', 'lock_enabled')
    exclude = ('type', 'layer_file', 'bbox_polygon')
    list_filter = ('lock_enabled', 'status')
    raw_id_fields = ("vrs",)

class LayerAdmin(admin.ModelAdmin):
    search_fields = ('title', 'status')
    exclude = ('type', 'document_file')
    list_filter = ('lock_enabled', )
    raw_id_fields = ("vrs",)

admin.site.register(Document, DocumentAdmin)
admin.site.register(LayerV1, LayerAdmin)

class DocumentLinkAdmin(admin.ModelAdmin):
    list_display = ['pk', 'source', 'target', 'link_type']
    list_filter = ('link_type', )

admin.site.register(DocumentLink, DocumentLinkAdmin)

class SessionLockAdmin(admin.ModelAdmin):
    raw_id_fields = ['session']

admin.site.register(SessionLock, SessionLockAdmin)
