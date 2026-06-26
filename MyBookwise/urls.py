"""Root URL configuration for MyBookwise."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.static import serve

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("bookstore.api.urls")),
    path("favicon.ico", serve, {"path": "favicon.ico", "document_root": settings.BASE_DIR}),
    path("", include("bookstore.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.BASE_DIR / "static")
