
1. Crear un Nuevo Proyecto
Para iniciar un nuevo proyecto en Django:

django-admin startproject nombre_del_proyecto

Esto creará una estructura de directorios con el proyecto base de Django.

2. Ejecutar el Servidor de Desarrollo
Una vez dentro de la carpeta del proyecto, puedes iniciar el servidor de desarrollo:

python manage.py runserver

El servidor estará disponible en http://127.0.0.1:8000 por defecto. Si deseas cambiar el puerto, usa:

python manage.py runserver 8080  # Cambia 8080 por el puerto que prefieras

3. Crear una Nueva Aplicación
Para crear una aplicación dentro del proyecto:

python manage.py startapp nombre_de_la_aplicacion

Cada aplicación puede representar un módulo o sección del sitio, como un blog, tienda, etc.

4. Migraciones de la Base de Datos

	a) Crear las Migraciones

	Después de modificar los modelos en las aplicaciones, crea una migración con:

	python manage.py makemigrations

	b) Aplicar las Migraciones

Para aplicar los cambios en la base de datos:

python manage.py migrate

5. Crear un Superusuario

Para acceder al panel de administración de Django, necesitas un superusuario:

python manage.py createsuperuser

Sigue las instrucciones para configurar el usuario y la contraseña.

6. Usar la Consola Interactiva de Django

Para probar o depurar código, puedes abrir la consola interactiva de Django:

python manage.py shell

Desde aquí puedes importar modelos y probar funcionalidades de la aplicación.

7. Administración y Gestión de Datos

	a) Crear Registros de Datos

	Desde la consola o código, puedes crear registros de la siguiente manera:

	from nombre_de_la_aplicacion.models import NombreDelModelo
	objeto = NombreDelModelo(campo1="valor", campo2="valor")
	objeto.save()
	b) Consultar Registros

	Para hacer consultas, puedes usar el ORM de Django:

	NombreDelModelo.objects.all()         # Todos los registros
	NombreDelModelo.objects.filter(...)   # Filtrar registros
	NombreDelModelo.objects.get(...)      # Obtener un registro específico

8. Crear Archivos de Pruebas (Tests)

Para crear pruebas unitarias en Django, define métodos de prueba en un archivo tests.py dentro de la aplicación. Luego, puedes ejecutar todas las pruebas con:

python manage.py test
9. Crear y Aplicar Archivos Estáticos y Plantillas

	a) Archivos Estáticos

	Para configurar y recopilar archivos estáticos, que pueden incluir imágenes, CSS, y JavaScript, ejecuta:

	python manage.py collectstatic
	b) Plantillas

Los archivos HTML de las plantillas deben estar en una carpeta templates dentro de cada aplicación o en el directorio principal del proyecto, configurando las rutas en el archivo settings.py.

10. Desplegar el Proyecto

Para entornos de producción, puedes utilizar gunicorn o uwsgi junto con un servidor web como Nginx o Apache. Antes de desplegar:

Asegúrate de cambiar DEBUG = False en settings.py.
Configura ALLOWED_HOSTS con los dominios o IPs permitidos.
Usa una configuración de base de datos adecuada para producción.
Resumen de Comandos Principales
Comando	Descripción
django-admin startproject	Crear un nuevo proyecto
python manage.py runserver	Iniciar el servidor de desarrollo
python manage.py startapp	Crear una nueva aplicación
python manage.py makemigrations	Crear migraciones de base de datos
python manage.py migrate	Aplicar migraciones a la base de datos
python manage.py createsuperuser	Crear un usuario administrador
python manage.py shell	Abrir la consola interactiva de Django
python manage.py test	Ejecutar pruebas unitarias
python manage.py collectstatic	Recopilar archivos estáticos
Estos comandos te ayudarán a manejar las tareas básicas de desarrollo en Django.