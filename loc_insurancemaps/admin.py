from django.contrib import admin

from .models import Volume, Sheet, FullThumbnail

admin.site.register(Sheet)
admin.site.register(FullThumbnail)

class VolumeAdmin(admin.ModelAdmin):
    exclude = ('lc_item', 'lc_resources')
    readonly_fields = ('lc_item_formatted', 'lc_resources_formatted')

admin.site.register(Volume, VolumeAdmin)
