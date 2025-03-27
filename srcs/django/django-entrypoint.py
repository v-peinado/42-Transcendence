from main.celery import setup_celery, get_worker_command, get_beat_command
from main.vault import load_vault_secrets
import subprocess
import logging
import django
import socket
import time
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configure Django settings module first
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "main.settings")


def wait_for_db(host, port):
    """Wait for the database service to be available"""
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


def verify_ssl_certificates():
    """Verify that SSL certificates are available and readable"""
    cert_file = "/tmp/ssl/transcendence.crt"
    key_file = "/tmp/ssl/transcendence.key"
    
    if not os.path.exists(cert_file):
        print(f"Error: SSL certificate file not found: {cert_file}")
        return False
    
    if not os.path.exists(key_file):
        print(f"Error: SSL key file not found: {key_file}")
        return False
    
    # Check if files are readable
    try:
        with open(cert_file, 'r') as f:
            cert_content = f.read()
            if not cert_content:
                print(f"Error: SSL certificate file is empty: {cert_file}")
                return False
    except Exception as e:
        print(f"Error reading SSL certificate file: {e}")
        return False
    
    print("SSL certificates verified successfully.")
    return True


def wait_for_vault(max_attempts=30):
    """Wait for the Vault secrets to be ready with exponential backoff"""
    
    print("Waiting for Vault secrets to be ready...")
    # Wait for Vault token file
    token_file = "/tmp/ssl/django_token"
    attempts = 0
    
    while attempts < max_attempts:
        if os.path.exists(token_file):
            print(f"Found token file after {attempts + 1} attempts")
            break
            
        wait_time = min(2 * (1.5 ** attempts), 10)  # Exponential backoff with max 10s
        print(f"Waiting for Vault token file... (Attempt {attempts + 1}/{max_attempts}, next wait: {wait_time:.1f}s)")
        attempts += 1
        time.sleep(wait_time)
    
    if not os.path.exists(token_file):
        print("Error: Vault token file not found")
        return False
    
    # Continue with vault client check
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


def check_system_user(username):
    """Check if the system user exists"""
    try:
        result = subprocess.run(
            ["id", "-u", username],
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode == 0 # Return True if user exists
    except Exception as e:
        print(f"Error checking system user: {e}")
        return False


def run_command(command, check=True):
    """Run a terminal command and return success status"""
    try:
        # Run command (see commands in the below functions of this file)
        process = subprocess.run(command, shell=True, text=True, check=check, capture_output=True)
        print(f"Successfully executed: {command}")
        return True, process.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error executing command (code {e.returncode}): {e.stderr}")
        return False, e.stderr


def start_celery_services(celery_user):
    """Start Celery worker and beat"""
    try:
        # Get commands from celery.py
        worker_cmd = get_worker_command(celery_user)
        beat_cmd = get_beat_command(celery_user)
        
        # Start worker
        worker_process = subprocess.Popen(worker_cmd, shell=True)
        
        # Start beat
        beat_process = subprocess.Popen(beat_cmd, shell=True)
        
        return worker_process, beat_process
    except Exception as e:
        print(f"Error starting Celery services: {e}")
        return None, None

def main():
    """Main function to start Django and Celery"""
    try:
        # Get environment variables
        db_host = os.getenv("SQL_HOST")
        if not db_host:
            logger.warning("SQL_HOST environment variable not set, using fallback 'db'")
            db_host = "db"
            
        db_port_str = os.getenv("SQL_PORT")
        if not db_port_str:
            logger.warning("SQL_PORT environment variable not set, using fallback '5432'")
            db_port_str = "5432"
        db_port = int(db_port_str)
        
        celery_user = os.getenv("CELERY_USER")
        if not celery_user:
            logger.warning("CELERY_USER environment variable not set, using fallback 'celeryuser'")
            celery_user = "celeryuser"
            
        use_daphne_str = os.getenv("USE_DAPHNE", "False")
        use_daphne = use_daphne_str.lower() == "true"

        # Verify required system user exists before starting services
        if not check_system_user(celery_user):
            print(f"Error: Required system user '{celery_user}' not found")
            sys.exit(1)
        print("Info: Required system user verified successfully")

        # Verify SSL certificates
        if not verify_ssl_certificates():
            print("Warning: SSL certificates verification failed")
            # Continue anyway as this is not a fatal error

        # Wait for services
        if not wait_for_db(db_host, db_port):
            sys.exit(1)

        if not wait_for_vault():
            sys.exit(1)

        # Setup Django
        django.setup()
        load_vault_secrets()

        # Run migrations directly
        run_command("python manage.py makemigrations")
        run_command("python manage.py makemigrations authentication")
        run_command("python manage.py makemigrations chat")
        run_command("python manage.py makemigrations tournament")
        run_command("python manage.py makemigrations game")
        run_command("python manage.py migrate --no-input")

        # Setup Celery (using the function from main.celery)
        if setup_celery():
            # Start Celery services
            worker_process, beat_process = start_celery_services(celery_user)
            if not worker_process or not beat_process:
                print("Error starting Celery services")
                sys.exit(1)
        else:
            print("Error setting up Celery environment")
            sys.exit(1)

        # Start Django server
        if use_daphne:
            # Start Daphne server
            os.execvp("daphne", ["daphne", "-b", "0.0.0.0", "-p", "8000", "main.asgi:application"])
        else:
            # Start Django development server
            os.execvp("python", ["python", "manage.py", "runserver", "0.0.0.0:8000"])

    except KeyboardInterrupt:
        print("Stopping services...")
        sys.exit(0)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
