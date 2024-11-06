import subprocess
import time
import socket

# Función para verificar si el servicio de base de datos está disponible
def wait_for_db(host, port):
    print(f"Esperando a que la base de datos en {host}:{port} esté lista...")
    while True:
        try:
            with socket.create_connection((host, port), timeout=2):
                print("Base de datos lista.")
                break
        except (ConnectionRefusedError, socket.timeout):
            print("Base de datos no está lista, esperando 2 segundos...")
            time.sleep(2)

# Función para ejecutar un comando en la terminal
def run_command(command):
    process = subprocess.run(command, shell=True, text=True)
    if process.returncode != 0:
        print(f"Error al ejecutar: {command}")
    else:
        print(f"Ejecutado con éxito: {command}")

# Espera a que el servicio de base de datos esté disponible
wait_for_db("db", 5432)

# Ejecuta las migraciones de Django
run_command("python manage.py makemigrations")
run_command("python manage.py migrate")

# Inicia el servidor de producción de Gunicorn
run_command("gunicorn main.wsgi:application --bind 0.0.0.0:8000")

