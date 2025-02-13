import socket
import time
import subprocess
import os
import sys


# Function to verify if the database service is available
def wait_for_db(host, port):
    print(f"Waiting for database at {host}:{port} to be ready...")
    retries = 0
    max_retries = 30  # Maximum wait time of 1 minute

    while retries < max_retries:
        try:
            with socket.create_connection((host, port), timeout=2):
                print("Database is ready.")
                return True
        except (ConnectionRefusedError, socket.timeout):
            print("Database not ready, waiting 2 seconds...")
            retries += 1
            time.sleep(2)

    print("Error: Could not connect to database after multiple attempts")
    return False


def wait_for_vault(max_attempts=30):
    print("Waiting for Vault secrets to be ready...")
    from main.vault import VaultClient

    client = VaultClient()

    for attempt in range(max_attempts):
        try:
            # Intenta leer un secreto conocido
            response = client.client.secrets.kv.v2.read_secret_version(
                path="django/database", mount_point="secret"
            )
            if response and response.get("data", {}).get("data"):
                print("Vault secrets are ready")
                return True
        except Exception:
            print(f"Vault not ready, waiting... ({attempt + 1}/{max_attempts})")
            time.sleep(2)

    print("Error: Could not connect to Vault after multiple attempts")
    return False


# Function to execute a terminal command
def run_command(command):
    try:
        process = subprocess.run(command, shell=True, text=True, check=True)
        print(f"Successfully executed: {command}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error executing: {command}")
        print(f"Error code: {e.returncode}")
        return False


def main():
    try:
        # Get environment variables
        db_host = os.getenv("SQL_HOST", "db")
        db_port = int(os.getenv("SQL_PORT", "5432"))

        # Wait for database to be available
        if not wait_for_db(db_host, db_port):
            print("Critical error: Could not connect to database")
            sys.exit(1)

        # Wait for Vault to be ready
        if not wait_for_vault():
            sys.exit(1)

        # Load secrets from Vault once at the start
        from main.vault import load_vault_secrets

        os.environ.pop("VAULT_SECRETS_LOADED", None)  # Forzar recarga de secretos
        load_vault_secrets()

        # Crear un script temporal para las migraciones
        with open("migrate.py", "w") as f:
            f.write(
                """
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "main.settings")
import django
django.setup()
from django.core.management import execute_from_command_line
execute_from_command_line(["", "makemigrations", "authentication", "chat", "game", "tournament", "--no-input"])
execute_from_command_line(["", "migrate", "--no-input"])
            """
            )

        # Ejecutar migraciones en un proceso separado
        if not run_command("python migrate.py"):
            print("Warning: Failed to apply migrations")

        # Limpiar
        os.remove("migrate.py")

        # Start Daphne
        if not run_command("daphne -b 0.0.0.0 -p 8000 main.asgi:application"):
            sys.exit(1)

    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
