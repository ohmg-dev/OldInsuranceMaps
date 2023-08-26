from django.contrib import admin
from ohmg.places.models import Place

class PlaceAdmin(admin.ModelAdmin):
    readonly_fields = ('display_name', 'slug')
    search_fields = ('display_name', 'slug')
    list_display = ('display_name', 'slug')
    list_filter = ('category',)

admin.site.register(Place, PlaceAdmin)