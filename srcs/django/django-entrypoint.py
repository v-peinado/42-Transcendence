import socket
import time
import subprocess
import os

# Función para verificar si el servicio de base de datos está disponible
def wait_for_db(host, port):
    print(f"Esperando a que la base de datos en {host}:{port} esté lista...")
    retries = 0
    max_retries = 30  # 1 minuto máximo de espera
    
    while retries < max_retries:
        try:
            with socket.create_connection((host, port), timeout=2):
                print("Base de datos lista.")
                return True
        except (ConnectionRefusedError, socket.timeout):
            print("Base de datos no está lista, esperando 2 segundos...")
            retries += 1
            time.sleep(2)
    
    print("Error: No se pudo conectar a la base de datos después de varios intentos")
    return False

# Función para ejecutar un comando en la terminal
def run_command(command):
    try:
        process = subprocess.run(command, shell=True, text=True, check=True)
        print(f"Ejecutado con éxito: {command}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error al ejecutar: {command}")
        print(f"Código de error: {e.returncode}")
        return False

def main():
    # Obtener variables de entorno
    db_host = os.getenv('SQL_HOST', 'db')
    db_port = int(os.getenv('SQL_PORT', '5432'))

    # Esperar a que la base de datos esté disponible
    if not wait_for_db(db_host, db_port):
        print("Error crítico: No se pudo conectar a la base de datos")
        exit(1)

    # Ejecutar migraciones
    if not run_command("python manage.py makemigrations"):
        exit(1)
    if not run_command("python manage.py migrate"):
        exit(1)

    # Iniciar Gunicorn con workers automáticos
    workers = (os.cpu_count() or 1) * 2 + 1
    gunicorn_cmd = f"daphne -b 0.0.0.0 -p 8000 main.asgi:application --verbosity 3"
    run_command(gunicorn_cmd)

if __name__ == "__main__":
    main()
		