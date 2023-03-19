from django.contrib import admin

from loc_insurancemaps.models import Volume, Sheet, Place

class SheetAdmin(admin.ModelAdmin):
    # search_fields = ('volume', 'sheet_no', 'doc')
    list_display = ('volume', 'sheet_no', 'doc')
    list_filter = ('volume', 'sheet_no', 'doc')
admin.site.register(Sheet, SheetAdmin)

class VolumeAdmin(admin.ModelAdmin):
    exclude = ('lc_item', 'lc_resources', 'document_lookup', 'layer_lookup', 'sorted_layers')
    readonly_fields = (
        'document_lookup_formatted',
        'layer_lookup_formatted',
        'sorted_layers_formatted',
        'lc_item_formatted',
        'lc_resources_formatted'
    )
    search_fields = ('city', 'volume_no', 'year')
    list_display = ('identifier', 'city', 'county_equivalent', 'volume_no', 'year', 'status')
    list_filter = ('identifier', 'city', 'county_equivalent', 'volume_no', 'year', 'status')

admin.site.register(Volume, VolumeAdmin)

class PlaceAdmin(admin.ModelAdmin):
    readonly_fields = ('display_name', 'slug')
    search_fields = ('display_name', 'slug')
    list_display = ('display_name', 'slug')
    list_filter = ('category',)

admin.site.register(Place, PlaceAdmin)
