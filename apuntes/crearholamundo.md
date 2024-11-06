Crear Hola Mundo en Django:

1. Instalación de Django
Primero, asegúrate de tener Python y pip instalados. Luego, puedes instalar Django usando pip.
pip install django

2. Crear un nuevo proyecto Django

django-admin startproject holamundo

Esto creará un directorio llamado holamundo con la estructura básica del proyecto.

3. Crear una nueva aplicación
Cambia al directorio del proyecto:
cd holamundo

Luego, crea una nueva aplicación dentro de tu proyecto. Por ejemplo, llamémosla miapp:
python manage.py startapp miapp

4. Configurar la aplicación
Ahora, abre el archivo settings.py que se encuentra en el directorio holamundo/holamundo/ y agrega la aplicación miapp a la lista de INSTALLED_APPS. Debería verse algo así:
INSTALLED_APPS = [
    ...
    'miapp',
]



5. Crear una vista
Abre el archivo views.py en el directorio miapp y define una vista simple que retorne "Hola, mundo":
from django.http import HttpResponse

def hola_mundo(request):
    return HttpResponse("Hola, mundo")

6. Configurar las URLs
Crea un archivo llamado urls.py en el directorio de miapp y define las URLs:
from django.urls import path
from .views import hola_mundo

urlpatterns = [
    path('', hola_mundo, name='hola_mundo'),
]

Luego, en el archivo urls.py del proyecto (en holamundo/holamundo/), incluye las URLs de la aplicación:
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('miapp.urls')),  # Agrega esta línea
]

7. Ejecutar el servidor
Ahora, puedes ejecutar el servidor de desarrollo para ver tu aplicación. Desde la terminal, ejecuta:
python manage.py runserver


8. Ver la página
Abre tu navegador web y ve a http://127.0.0.1:8000/. Deberías ver el mensaje "Hola, mundo".
9. Estructura del proyecto
Esto es si usamos Docker en vez de venv. 

/tu_proyecto
│
├── Dockerfile
├── requirements.txt
└── tu_proyecto_django/
    ├── hola_mundo/          # Nueva aplicación
    │   ├── __init__.py
    │   ├── admin.py
    │   ├── apps.py
    │   ├── migrations/
    │   ├── models.py
    │   ├── tests.py
    │   ├── views.py         # Aquí está la vista
    ├── manage.py
    └── tu_proyecto/
        ├── __init__.py
        ├── settings.py
        ├── urls.py          # Aquí se configuran las rutas
        └── wsgi.py

requirements.txt son las configuraciones que necesitará docker para configurar django, al montar su imagen. Solo habría que pegar esto dentro de ese .txt para poder levantar esta página:
Django>=4.0,<5.0
