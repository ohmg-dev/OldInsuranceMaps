from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path
from django.views.defaults import page_not_found, server_error

from ohmg.api.routes import beta2


def debug_page_not_found(request):
    return page_not_found(request, None)


# this one doesn't work yet...
def debug_server_error(request):
    return server_error(request)


urlpatterns = [
    ## OHMG app urls
    path("", include("ohmg.frontend.urls")),
    path("", include("ohmg.core.urls")),
    path("", include("ohmg.accounts.urls")),
    path("", include("ohmg.georeference.urls")),
    path("", include("ohmg.extensions.urls")),
    path("", include("ohmg.places.urls")),
    ## Django extensions URLs
    path("grappelli/", include("grappelli.urls")),
    path("admin/", admin.site.urls, name="admin"),
    path("avatar/", include("avatar.urls")),
    path("api/beta2/", beta2.urls),
    path("markdownx/", include("markdownx.urls")),
]

urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.VRT_URL, document_root=settings.VRT_ROOT)

if "pinax.announcements" in settings.INSTALLED_APPS:
    urlpatterns += [
        path(
            "announcements/",
            include("pinax.announcements.urls", namespace="pinax_announcements"),
        )
    ]

if settings.DEBUG:
    urlpatterns += [
        path("404/", debug_page_not_found),
        path("500/", debug_server_error),
    ]

if settings.ENABLE_DEBUG_TOOLBAR:
    urlpatterns += [path("__debug__/", include("debug_toolbar.urls"))]
