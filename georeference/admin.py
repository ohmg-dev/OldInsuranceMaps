from django.contrib import admin

from georeference.models.resources import (
    SplitDocumentLink,
    GeoreferencedDocumentLink,
    GCP,
    GCPGroup,
    Layer,
    Document,
    DocumentLink,
)
from georeference.models.sessions import (
    PrepSession,
    GeorefSession,
    TrimSession,
)

class GCPAdmin(admin.ModelAdmin):
    readonly_fields = ('last_modified',)
    list_display = ('id', 'gcp_group')

admin.site.register(SplitDocumentLink)
admin.site.register(GeoreferencedDocumentLink)
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
admin.site.register(TrimSession, TrimSessionAdmin)

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
