from main.vault import load_vault_secrets
import subprocess
import logging
import django
import shutil
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


def setup_static_files():
    """Create and setup directories for static files"""
    try:
        # Create directories
        os.makedirs("/app/static_custom", exist_ok=True)
        
        # Clear static files and collect new ones
        static_dir = "/app/static"
        if os.path.exists(static_dir):
            for item in os.listdir(static_dir):
                item_path = os.path.join(static_dir, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
        
        success, _ = run_command("python manage.py collectstatic --noinput --clear")
        return success
    except Exception as e:
        print(f"Error setting up static files: {e}")
        return False


def setup_celery(celery_user):
    """Setup directories and permissions for Celery"""
    try:
        # Create required directories
        os.makedirs("/var/lib/celery", exist_ok=True)
        
        # Set ownership
        run_command(f"chown -R {celery_user}:{celery_user} /var/lib/celery")
        
        # Export environment variable for Celery beat
        os.environ["CELERYBEAT_SCHEDULE_FILENAME"] = "/var/lib/celery/celerybeat-schedule"
        
        return True
    except Exception as e:
        print(f"Error setting up Celery: {e}")
        return False


def start_celery_services(celery_user):
    """Start Celery worker and beat"""
    try:
        # Start worker with the celery user
        worker_cmd = f"su -m {celery_user} -c 'celery -A main worker --loglevel=info'"
        worker_process = subprocess.Popen(worker_cmd, shell=True)
        
        # Start beat with the celery user
        beat_cmd = f"su -m {celery_user} -c 'celery -A main beat --loglevel=info --schedule=/var/lib/celery/celerybeat-schedule'"
        beat_process = subprocess.Popen(beat_cmd, shell=True)
        
        return worker_process, beat_process
    except Exception as e:
        print(f"Error starting Celery services: {e}")
        return None, None

# Worker is a process that runs the tasks in the background
# Beat is a process that schedules tasks to be executed at a specific time
# The worker and beat are started as separate processes to run in parallel with the Django server
# but started in the same container with celery user

def main():
    """Main function to start Django and Celery"""
    try:
        # Get environment variables
        db_host = os.getenv("SQL_HOST", "db")
        db_port = int(os.getenv("SQL_PORT", "5432"))
        celery_user = os.getenv("CELERY_USER", "celeryuser")
        use_daphne = os.getenv("USE_DAPHNE", "False").lower() == "true"

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

        # Setup static files
        setup_static_files()

        # Run migrations directly
        run_command("python manage.py makemigrations")
        run_command("python manage.py makemigrations authentication")
        run_command("python manage.py makemigrations chat")
        run_command("python manage.py makemigrations tournament")
        run_command("python manage.py makemigrations game")
        run_command("python manage.py migrate --no-input")

        # Setup Celery
        if setup_celery(celery_user):
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
