from django.contrib import admin

from .models import (
    SplitDocumentLink,
    GeoreferencedDocumentLink,
    SplitEvaluation,
    GeoreferenceSession,
    GCP,
    GCPGroup,
    LayerMask,
    MaskSession,
)

class GCPAdmin(admin.ModelAdmin):
    readonly_fields = ('last_modified',)

class GeoreferenceSessionAdmin(admin.ModelAdmin):
    readonly_fields = ('created',)

admin.site.register(SplitDocumentLink)
admin.site.register(SplitEvaluation)
admin.site.register(GeoreferencedDocumentLink)
admin.site.register(GeoreferenceSession, GeoreferenceSessionAdmin)
admin.site.register(GCP, GCPAdmin)
admin.site.register(GCPGroup)
admin.site.register(LayerMask)
admin.site.register(MaskSession)
