from django.contrib import admin
from django.db.models import JSONField
from django_json_widget.widgets import JSONEditorWidget
from markdownx.admin import MarkdownxModelAdmin

from .models import Navbar, Page, Partner, Redirect


class PageAdmin(MarkdownxModelAdmin):
    readonly_fields = ["slug", "date_published", "date_modified"]


admin.site.register(Page, PageAdmin)


class NavbarAdmin(admin.ModelAdmin):
    formfield_overrides = {
        JSONField: {"widget": JSONEditorWidget},
    }


admin.site.register(Navbar, NavbarAdmin)


class PartnerAdmin(admin.ModelAdmin):
    list_display = ("name", "sortorder", "published", "description")


admin.site.register(Partner, PartnerAdmin)


class RedirectAdmin(admin.ModelAdmin):
    list_display = ("src", "dest")


admin.site.register(Redirect, RedirectAdmin)
