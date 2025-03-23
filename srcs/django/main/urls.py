"""URL configuration for main project."""

from django.core.exceptions import ImproperlyConfigured
from django.conf.urls.static import static
from django.urls import path, include
from django.contrib import admin
from django.conf import settings
import os

# Check if basic configuration is correct
if "authentication" not in settings.INSTALLED_APPS:
    raise ImproperlyConfigured("The 'authentication' app must be in INSTALLED_APPS")

# Check if the environment is production
def check_nginx_config():
    if not os.environ.get("DJANGO_DEVELOPMENT", False):  # Production environment check (put in .env)
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
    # API tournament
    path('api/tournament/', include('tournament.urls')),
    # API endpoints (production)
    path("api/", include("authentication.api.urls")),
    # Game
    path("game/", include("game.urls")),
    # API dashboard
    path('api/dashboard/', include('dashboard.urls')),
]

# Media and static files configuration
if settings.DEBUG:
    # Serve media files in development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    check_nginx_config()
