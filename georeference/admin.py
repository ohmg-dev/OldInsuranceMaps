from django.contrib import admin

from .models import (
    SplitDocumentLink,
    GeoreferencedDocumentLink,
    GCP,
    GCPGroup,
    LayerMask,
    PrepSession,
    GeorefSession,
    TrimSession,
)

class GCPAdmin(admin.ModelAdmin):
    readonly_fields = ('last_modified',)
    list_display = ('__str__',)

admin.site.register(SplitDocumentLink)
admin.site.register(GeoreferencedDocumentLink)
admin.site.register(GCP, GCPAdmin)
admin.site.register(GCPGroup)
admin.site.register(LayerMask)

class SessionAdmin(admin.ModelAdmin):
    readonly_fields = ('date_created', 'date_modified', 'date_run')
    list_display = ['__str__', 'document', 'layer', 'user', 'stage', 'status', 'note', 'date_created', 'date_modified', 'date_run']
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
