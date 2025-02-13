"""URL configuration for main project."""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.core.exceptions import ImproperlyConfigured
import os
import warnings
from chat import views

# Check basic configuration
if "authentication" not in settings.INSTALLED_APPS:
    raise ImproperlyConfigured("The 'authentication' app must be in INSTALLED_APPS")


def check_nginx_config():
    if not os.environ.get("DJANGO_DEVELOPMENT", False):  # Solo verificar en producción
        media_path = "/usr/share/nginx/html/media"
        if not os.path.exists(media_path):
            os.makedirs(media_path, exist_ok=True)
            os.chmod(media_path, 0o755)


# Main URL patterns
urlpatterns = [
    # Web interface (development)
    path("", include("authentication.web.urls")),
    # Admin panel
    path("admin/", admin.site.urls),
    # Tournament API
    # path('api/tournament/', include('tournament.api.urls')),
    # API endpoints (production)
    path("api/", include("authentication.api.urls")),
    # Chat
    path("chat/", views.chat, name="chat"),
    # Game
    path("game/", include("game.urls")),
]

# Media and static files configuration
if settings.DEBUG:
    # Serve media files in development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Serve static files in development
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
else:
    check_nginx_config()
