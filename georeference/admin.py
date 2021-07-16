from django.contrib import admin

from .models import SplitSession, SplitLink, GCP, GCPGroup

class GCPAdmin(admin.ModelAdmin):
    readonly_fields = ('last_modified',)

admin.site.register(SplitLink)
admin.site.register(SplitSession)
admin.site.register(GCP, GCPAdmin)
admin.site.register(GCPGroup)
