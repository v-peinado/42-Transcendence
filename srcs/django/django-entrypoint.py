import subprocess

# Función para ejecutar un comando en la terminal
def run_command(command):
    process = subprocess.run(command, shell=True, text=True)
    if process.returncode != 0:
        print(f"Error al ejecutar: {command}")
    else:
        print(f"Ejecutado con éxito: {command}")

# Ejecuta las migraciones de Django
run_command("python manage.py makemigrations")
run_command("python manage.py migrate")

# Inicia el servidor de desarrollo de Django
# run_command("python manage.py runserver 0.0.0.0:8000")

# Inicia el servidor de producción de Gunicorn, es mas rápido que el servidor de desarrollo y es recomendado para producción
run_command("gunicorn main.wsgi:application --bind 0.0.0.0:8000")
