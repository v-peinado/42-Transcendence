"""URL configuration for main project."""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.core.exceptions import ImproperlyConfigured
import os
import warnings
from chat import views

# Verificar configuración básica
if 'authentication' not in settings.INSTALLED_APPS:
    raise ImproperlyConfigured("La aplicación 'authentication' debe estar en INSTALLED_APPS")

def check_nginx_config():
    """Verifica la configuración de Nginx para servir archivos media"""
    nginx_media_path = "/usr/share/nginx/html/media"
    if not settings.DEBUG and not os.path.exists(nginx_media_path):
        raise RuntimeWarning(
            "\n¡ERROR DE CONFIGURACIÓN!"
            "\nNginx no está configurado correctamente para servir archivos media."
            f"\nNo se encuentra el directorio: {nginx_media_path}"
            "\n"
            "\nAsegúrate de:"
            "\n1. Tener Nginx instalado y configurado"
            "\n2. Tener el volumen django_media montado correctamente"
            "\n3. Configurar la ruta correcta en nginx.conf"
        )

# URL patterns principales
urlpatterns = [
    # Interfaz web (desarrollo)
    path('', include('authentication.web.urls')),
    
    # Panel de administración
    path('admin/', admin.site.urls),
    
    # API de tournament
    path('api/tournament/', include('tournament.urls')),
    
    # API endpoints (producción)
    path('api/', include('authentication.api.urls')),
    
    #chat
    path('chat/', views.chat, name='chat'),
    
    # game
    path('game/', include('game.urls')),
]

# Configuración de archivos media y estáticos
if settings.DEBUG:
    # Servir archivos media en desarrollo
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Servir archivos estáticos en desarrollo
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
else:
    check_nginx_config()