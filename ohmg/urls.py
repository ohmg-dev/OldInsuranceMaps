from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path
from django.contrib.sitemaps.views import sitemap
from django.views.defaults import page_not_found, server_error
from django.views.generic import TemplateView, RedirectView

from ohmg.core.api.routes import beta2
from .sitemap import sitemaps


def debug_page_not_found(request):
    return page_not_found(request, None)


# this one doesn't work yet...
def debug_server_error(request):
    return server_error(request)


urlpatterns = [
    ## OHMG urls
    path("", include("ohmg.content.urls")),
    path("", include("ohmg.core.urls")),
    path("", include("ohmg.accounts.urls")),
    path("", include("ohmg.georeference.urls")),
    path("", include("ohmg.iiif.urls")),
    path("", include("ohmg.places.urls")),
    ## Standard URLs
    path(
        "robots.txt",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
    ),
    path(
        "favicon.ico",
        RedirectView.as_view(url=settings.STATIC_URL + "favicon.ico", permanent=True),
    ),
    path(
        "sitemap.xml/",
        sitemap,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),
    ## Django extensions URLs
    path("grappelli/", include("grappelli.urls")),
    path("admin/", admin.site.urls, name="admin"),
    path("account/", include("allauth.urls")),
    path("avatar/", include("avatar.urls")),
    path("api/beta2/", beta2.urls),
    path("markdownx/", include("markdownx.urls")),
]

urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.VRT_URL, document_root=settings.VRT_ROOT)


## Optionally included URLs
if settings.ENABLE_NEWSLETTER:
    urlpatterns += [path("newsletter/", include("newsletter.urls"))]

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
