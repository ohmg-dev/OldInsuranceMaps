from django.contrib import admin

from ohmg.georeference.models import (
    GCP,
    GCPGroup,
    PrepSession,
    GeorefSession,
    SessionLock,
)


class GCPAdmin(admin.ModelAdmin):
    readonly_fields = ("last_modified",)
    list_display = ("id", "gcp_group")


class GCPGroupAdmin(admin.ModelAdmin):
    raw_id_fields = ("region2",)


admin.site.register(GCP, GCPAdmin)
admin.site.register(GCPGroup, GCPGroupAdmin)


class SessionAdmin(admin.ModelAdmin):
    raw_id_fields = ("doc2", "reg2", "lyr2")
    readonly_fields = ("map", "date_created", "date_modified", "date_run")
    list_display = [
        "__str__",
        "user",
        "stage",
        "status",
        "note",
        "date_created",
        "date_modified",
        "date_run",
    ]
    list_filter = ("stage",)


class PrepSessionAdmin(SessionAdmin):
    exclude = ("type",)


class GeorefSessionAdmin(SessionAdmin):
    exclude = ("type",)


admin.site.register(PrepSession, PrepSessionAdmin)
admin.site.register(GeorefSession, GeorefSessionAdmin)


class SessionLockAdmin(admin.ModelAdmin):
    raw_id_fields = ["session"]


admin.site.register(SessionLock, SessionLockAdmin)
