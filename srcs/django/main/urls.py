"""URL configuration for main project."""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
import os
import warnings

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

""" Configuración de las URLs de la aplicación web principal """
urlpatterns = [
    # Web interface URLs
    path('', include('authentication.web.urls')),
    
    # Admin interface
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/', include('authentication.api.urls')),
]

""" Configuración de la entrega de archivos multimedia en entornos de desarrollo """
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    check_nginx_config()

"""
Este archivo define las URL de la aplicación web principal.

Hay dos funciones importantes en este archivo: path() y include().
path() se utiliza para definir una URL y la vista asociada.
include() se utiliza para incluir otras URLconf.

Estamos incluyendo las URL de la aplicación web de autenticación (desarrollo) y las URL de la API (producción).
También estamos incluyendo las URL de la interfaz de administración de Django.

Además, estamos configurando la entrega de archivos multimedia en entornos de desarrollo (DEBUG=True)
a través de Django.

Hay una advertencia que se mostrará si la configuración de Nginx no está configurada correctamente 
para servir archivos multimedia y si ya estamos en producción (DEBUG=False).
"""