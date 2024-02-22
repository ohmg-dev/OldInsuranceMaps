from django.contrib import admin
from markdownx.admin import MarkdownxModelAdmin

from ohmg.content.models import Page


class PageAdmin(MarkdownxModelAdmin):
    readonly_fields = ['slug']


admin.site.register(Page, PageAdmin)