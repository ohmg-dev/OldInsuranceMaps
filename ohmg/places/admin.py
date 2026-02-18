from django.contrib import admin

from ohmg.places.models import Place, ReferenceLayer


class PlaceAdmin(admin.ModelAdmin):
    autocomplete_fields = ("direct_parents",)
    readonly_fields = ("display_name", "slug")
    search_fields = ("display_name", "slug")
    list_display = ("display_name", "slug")
    list_filter = ("category",)


admin.site.register(Place, PlaceAdmin)


class ReferenceLayerAdmin(admin.ModelAdmin):
    autocomplete_fields = ("locale",)


admin.site.register(ReferenceLayer, ReferenceLayerAdmin)
