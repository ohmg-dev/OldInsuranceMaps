from django.contrib import admin


class SheetAdmin(admin.ModelAdmin):
    # search_fields = ('volume', 'sheet_no', 'doc')
    list_display = ("volume", "sheet_no", "doc")
    list_filter = ("volume", "sheet_no", "doc")
    raw_id_fields = ("volume", "doc")


# admin.site.register(Sheet, SheetAdmin)


class VolumeAdmin(admin.ModelAdmin):
    exclude = ("lc_item", "lc_resources", "document_lookup", "layer_lookup")
    readonly_fields = (
        "document_lookup_formatted",
        "layer_lookup_formatted",
        "lc_item_formatted",
        "lc_resources_formatted",
    )
    search_fields = ("city", "volume_no", "year")
    list_display = (
        "identifier",
        "city",
        "county_equivalent",
        "volume_no",
        "year",
        "status",
    )
    list_filter = (
        "identifier",
        "city",
        "county_equivalent",
        "volume_no",
        "year",
        "status",
    )
    autocomplete_fields = ("locales",)


# admin.site.register(Volume, VolumeAdmin)
