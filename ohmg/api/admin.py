from django.contrib import admin

from ohmg.api.models import Key

class KeyAdmin(admin.ModelAdmin):
    list_display = ('value', 'account', 'active', 'request_count')
    readonly_fields = ('value', 'request_count')

admin.site.register(Key, KeyAdmin)
