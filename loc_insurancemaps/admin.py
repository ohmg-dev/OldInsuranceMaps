from django.contrib import admin

from modeltranslation.admin import TabbedTranslationAdmin
from .models import Volume, Sheet, FullThumbnail

from geonode.base.admin import ResourceBaseAdminForm
from geonode.base.admin import metadata_batch_edit


admin.site.register(Sheet)
admin.site.register(FullThumbnail)

class VolumeAdmin(admin.ModelAdmin):
    exclude = ('lc_item', 'lc_resources')
    readonly_fields = ('lc_item_formatted', 'lc_resources_formatted')

admin.site.register(Volume, VolumeAdmin)

# class MapScanAdminForm(ResourceBaseAdminForm):
#     class Meta(ResourceBaseAdminForm.Meta):
#         model = MapScan
#         fields = '__all__'
#         # exclude = (
#         #     'resource',
#         # )


# class MapScanAdmin(TabbedTranslationAdmin):
#     exclude = ('doc_type',)
#     list_display = ('id',
#                     'title',
#                     'date',
#                     'category',
#                     'group',
#                     'is_approved',
#                     'is_published',
#                     'metadata_completeness')
#     list_display_links = ('id',)
#     list_editable = ('title', 'category', 'group', 'is_approved', 'is_published')
#     list_filter = ('date', 'date_type', 'restriction_code_type', 'category',
#                    'group', 'is_approved', 'is_published',)
#     search_fields = ('title', 'abstract', 'purpose',
#                      'is_approved', 'is_published',)
#     date_hierarchy = 'date'
#     form = MapScanAdminForm
#     actions = [metadata_batch_edit]

# admin.site.register(MapScan, MapScanAdmin)

# class MapCollectionItemAdminForm(ResourceBaseAdminForm):
#     class Meta(ResourceBaseAdminForm.Meta):
#         model = MapCollectionItem
#         fields = '__all__'
#         # exclude = (
#         #     'resource',
#         # )


# class MapCollectionItemAdmin(TabbedTranslationAdmin):
#     list_display = ('id',
#                     'title',
#                     'date',
#                     'category',
#                     'group',
#                     'is_approved',
#                     'is_published',
#                     'metadata_completeness')
#     list_display_links = ('id',)
#     list_editable = ('title', 'category', 'group', 'is_approved', 'is_published')
#     list_filter = ('date', 'date_type', 'restriction_code_type', 'category',
#                    'group', 'is_approved', 'is_published',)
#     search_fields = ('title', 'abstract', 'purpose',
#                      'is_approved', 'is_published',)
#     date_hierarchy = 'date'
#     form = MapScanAdminForm
#     actions = [metadata_batch_edit]

# admin.site.register(MapCollectionItem, MapCollectionItemAdmin)
