from django.contrib import admin

from .models import (
    SplitSession,
    Segmentation,
    SplitDocumentLink,
    GeoreferenceSession,
    GCP,
    GCPGroup,
)

class GCPAdmin(admin.ModelAdmin):
    readonly_fields = ('last_modified',)

class GeoreferenceSessionAdmin(admin.ModelAdmin):
    readonly_fields = ('created',)

admin.site.register(SplitDocumentLink)
admin.site.register(Segmentation)
admin.site.register(SplitSession)
admin.site.register(GeoreferenceSession, GeoreferenceSessionAdmin)
admin.site.register(GCP, GCPAdmin)
admin.site.register(GCPGroup)
