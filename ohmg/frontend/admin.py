from django.contrib import admin

from markdownx.admin import MarkdownxModelAdmin
from django.db.models import JSONField
from django_json_widget.widgets import JSONEditorWidget

from .models import Page, Navbar


class PageAdmin(MarkdownxModelAdmin):
    readonly_fields = ["slug", "date_published", "date_modified"]


admin.site.register(Page, PageAdmin)


class NavbarAdmin(admin.ModelAdmin):
    formfield_overrides = {
        JSONField: {"widget": JSONEditorWidget},
    }


admin.site.register(Navbar, NavbarAdmin)
