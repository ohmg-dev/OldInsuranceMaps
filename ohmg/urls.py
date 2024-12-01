from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path
from django.contrib.sitemaps.views import sitemap
from django.views.generic import TemplateView

from ohmg.core.api.routes import beta2
from .sitemap import sitemaps

urlpatterns = [
    path("", include("ohmg.content.urls")),
    path("", include("ohmg.frontend.urls")),
    path("", include("ohmg.accounts.urls")),
    path("", include("ohmg.georeference.urls")),
    path("", include("ohmg.iiif.urls")),
    path("forum-embed-test/", TemplateView.as_view(template_name="forum-embed.html")),
    path("admin/", admin.site.urls, name="admin"),
    path("account/", include("allauth.urls")),
    path("avatar/", include("avatar.urls")),
    path("api/beta2/", beta2.urls),
    path("markdownx/", include("markdownx.urls")),
    path(
        "sitemap.xml/",
        sitemap,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),
]

if settings.ENABLE_NEWSLETTER:
    urlpatterns += [path("newsletter/", include("newsletter.urls"))]

if "pinax.announcements" in settings.INSTALLED_APPS:
    urlpatterns += [
        path(
            "announcements/",
            include("pinax.announcements.urls", namespace="pinax_announcements"),
        )
    ]

# this places path must be the last url that is tried, because it is a total wildcard.
urlpatterns += [path("", include("ohmg.places.urls"))]

urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.ENABLE_DEBUG_TOOLBAR:
    urlpatterns += [path("__debug__/", include("debug_toolbar.urls"))]
