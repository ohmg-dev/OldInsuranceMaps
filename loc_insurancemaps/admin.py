from django.contrib import admin

from loc_insurancemaps.models import Volume, Sheet, FullThumbnail, Place

admin.site.register(Sheet)
admin.site.register(FullThumbnail)


class VolumeAdmin(admin.ModelAdmin):
    exclude = ('lc_item', 'lc_resources')
    readonly_fields = ('lc_item_formatted', 'lc_resources_formatted')
    search_fields = ('city', 'volume_no', 'year')
    list_display = ('identifier', 'city', 'county_equivalent', 'volume_no', 'year', 'status')
    list_filter = ('identifier', 'city', 'county_equivalent', 'volume_no', 'year', 'status')

admin.site.register(Volume, VolumeAdmin)

class PlaceAdmin(admin.ModelAdmin):
    readonly_fields = ('display_name', 'slug')
    list_filter = ('category',)

admin.site.register(Place, PlaceAdmin)
