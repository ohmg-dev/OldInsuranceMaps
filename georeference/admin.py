from django.contrib import admin

from .models import (
    SplitSession,
    SplitLink,
    GeoreferenceSession,
    GCP,
    GCPGroup,
)

class GCPAdmin(admin.ModelAdmin):
    readonly_fields = ('last_modified',)

class GeoreferenceSessionAdmin(admin.ModelAdmin):
    readonly_fields = ('created',)

admin.site.register(SplitLink)
admin.site.register(SplitSession)
admin.site.register(GeoreferenceSession, GeoreferenceSessionAdmin)
admin.site.register(GCP, GCPAdmin)
admin.site.register(GCPGroup)
