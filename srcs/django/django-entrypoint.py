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

        # Execute specific migrations first
        apps = ["authentication", "chat", "game", "tournament"]
        for app in apps:
            if not run_command(f"python manage.py makemigrations {app}"):
                sys.exit(1)

        # Apply all migrations
        if not run_command("python manage.py migrate"):
            sys.exit(1)

        # Start Daphne
        gunicorn_cmd = f"daphne -b 0.0.0.0 -p 8000 main.asgi:application --verbosity 3"
        if not run_command(gunicorn_cmd):
            sys.exit(1)

    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
