import socket
import time
import subprocess
import os
import sys
import django
from main.vault import load_vault_secrets

# Configure Django settings module first
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "main.settings")


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
    from main.vault import get_client, wait_for_secrets

    client = get_client()
    if not client:
        print("Failed to initialize Vault client")
        return False

    # Try to read a test secret
    secrets = wait_for_secrets(client, "django/database")
    if secrets:
        print("Successfully verified Vault access")
        return True

    print("Failed to verify Vault access")
    return False


# Function to execute a terminal command
def run_command(command):
    try:
        subprocess.run(command, shell=True, text=True, check=True)
        print(f"Successfully executed: {command}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error executing command (code {e.returncode})")
        return False


def main():
    """Main function to start Django and Celery"""
    try:
        # Get environment variables
        db_host = os.getenv("SQL_HOST", "db")
        db_port = int(os.getenv("SQL_PORT", "5432"))

        # Wait for services
        if not wait_for_db(db_host, db_port):
            sys.exit(1)

        if not wait_for_vault():
            sys.exit(1)

        django.setup()

        load_vault_secrets()

        # Run migrations directly
        if not run_command(
            "python manage.py makemigrations authentication chat game tournament --no-input"
        ):
            print("Warning: Failed to make migrations")
        if not run_command("python manage.py migrate --no-input"):
            print("Warning: Failed to apply migrations")

        # Start Celery worker in background
        celery_worker = subprocess.Popen(
            ["celery", "-A", "main", "worker", "--loglevel=info"],
            stdout=sys.stdout,
            stderr=sys.stderr
        )
        
        # Start Celery beat in background
        celery_beat = subprocess.Popen(
            ["celery", "-A", "main", "beat", "--loglevel=info"],
            stdout=sys.stdout,
            stderr=sys.stderr
        )

        # Start Django server (this will block)
        os.execvp("python", ["python", "manage.py", "runserver", "0.0.0.0:8000"])

    except KeyboardInterrupt:
        print("Stopping services...")
        celery_worker.terminate()
        celery_beat.terminate()
        sys.exit(0)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
