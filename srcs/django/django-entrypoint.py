import socket
import time
import subprocess
import os

def run_command(command):
    """
    Ejecuta un comando en la terminal y devuelve True si fue exitoso.
    Parámetros:
        command: Comando a ejecutar
        shell=True: Permite ejecutar comandos del shell
        text=True: Maneja la salida como texto
        check=True: Lanza excepción si el comando falla
    """
    try:
        process = subprocess.run(command, shell=True, text=True, check=True)
        print(f"Ejecutado con éxito: {command}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error al ejecutar: {command}")
        print(f"Código de error: {e.returncode}")
        return False


def wait_for_db(host, port):
    """
    Espera a que la base de datos esté disponible en la dirección y puerto especificados.
    Parámetros:
		host: Dirección IP o nombre de host de la base de datos
		port: Puerto de la base de datos
	"""
    print(f"Esperando a que la base de datos en {host}:{port} esté lista...")
    retries = 0
    max_retries = 30  # Máximo 30 intentos (60 segundos en total)
    
    while retries < max_retries:
        try:
            # Intenta establecer conexión con la base de datos (timeout 2s)
            with socket.create_connection((host, port), timeout=2):
                print("Base de datos lista.")
                return True
        except (ConnectionRefusedError, socket.timeout):
            print("Base de datos no está lista, esperando 2 segundos...")
            retries += 1
            time.sleep(2)  # Pausa entre intentos
    
    print("Error: No se pudo conectar a la base de datos después de varios intentos")
    return False


def main():
    """
    Punto de entrada principal para la aplicación Django.
    """
    # Obtener variables de entorno para la conexión a la base de datos
    db_host = os.getenv('SQL_HOST', 'db')
    db_port = int(os.getenv('SQL_PORT', '5432'))

    # Esperar a que la base de datos esté disponible antes de ejecutar migraciones
    if not wait_for_db(db_host, db_port):
        print("Error crítico: No se pudo conectar a la base de datos")
        exit(1)

    # Ejecutar migraciones 
    if not run_command("python manage.py makemigrations"):
        exit(1)
    if not run_command("python manage.py migrate"):
        exit(1)

    # Iniciar Gunicorn con workers automáticos (2 * CPU + 1 por recomendación de Gunicorn)
    workers = (os.cpu_count() or 1) * 2 + 1
    gunicorn_cmd = f"gunicorn main.wsgi:application --bind 0.0.0.0:8000 --workers {workers}"
    run_command(gunicorn_cmd)

if __name__ == "__main__":	
    main()				