from django.contrib import admin

from ohmg.georeference.models import (
    GCP,
    GCPGroup,
    Layer,
    Document,
    DocumentLink,
    PrepSession,
    GeorefSession,
    # ItemBase,
    # VirtualResourceSet,
    # VirtualResourceSetType,
)

# class VRSAdmin(admin.ModelAdmin):
#     readonly_fields = (
#         'vres_list',
#     )

# admin.site.register(VirtualResourceSet, VRSAdmin)
# admin.site.register(VirtualResourceSetType)
# admin.site.register(ItemBase)

class GCPAdmin(admin.ModelAdmin):
    readonly_fields = ('last_modified',)
    list_display = ('id', 'gcp_group')

admin.site.register(GCP, GCPAdmin)
admin.site.register(GCPGroup)

class SessionAdmin(admin.ModelAdmin):
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

class LayerAdmin(admin.ModelAdmin):
    search_fields = ('title', 'status')
    exclude = ('type', 'document_file')
    list_filter = ('lock_enabled', )

admin.site.register(Document, DocumentAdmin)
admin.site.register(Layer, LayerAdmin)

class DocumentLinkAdmin(admin.ModelAdmin):
    list_display = ['pk', 'source', 'target', 'link_type']
    list_filter = ('link_type', )

admin.site.register(DocumentLink, DocumentLinkAdmin)
