from django.conf import settings
from celery import Celery
import subprocess
import logging
import shutil
import os

# Set the default Django settings module for the 'celery' program.
# This is the same as the DJANGO_SETTINGS_MODULE environment variable 
# but we put it here to maintain the configuration in the same file.

# Celery 6.0 specific configuration (see https://docs.celeryproject.org/en/stable/whatsnew-6.0.html)
logger = logging.getLogger(__name__)

# Configure the environment for django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')

# Create the Celery application
app = Celery('main')

# Load configuration from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

def configure_ssl_certificates(celery_user=None):
    """Set up SSL certificates for PostgreSQL connections"""
    if not celery_user:
        celery_user = os.environ.get("CELERY_USER")
        if not celery_user:
            logger.warning("CELERY_USER environment variable not set, using fallback 'celeryuser'")
            celery_user = "celeryuser"
    
    logger.info(f"Configuring SSL certificates for PostgreSQL using {celery_user}")
    
    try:
        # Create PostgreSQL certificate directory for Celery
        postgres_cert_dir = f"/home/{celery_user}/.postgresql"
        os.makedirs(postgres_cert_dir, exist_ok=True)
        
        # Copy SSL certificates for PostgreSQL
        ssl_src_dir = "/tmp/ssl"
        if os.path.exists(f"{ssl_src_dir}/transcendence.crt") and os.path.exists(f"{ssl_src_dir}/transcendence.key"):
            # Copy to celeryuser's directory
            shutil.copy(f"{ssl_src_dir}/transcendence.crt", f"{postgres_cert_dir}/postgresql.crt")
            shutil.copy(f"{ssl_src_dir}/transcendence.key", f"{postgres_cert_dir}/postgresql.key")
            
            # Set permissions for PostgreSQL certificates
            subprocess.run(f"chmod 600 {postgres_cert_dir}/postgresql.crt", shell=True, check=True)
            subprocess.run(f"chmod 600 {postgres_cert_dir}/postgresql.key", shell=True, check=True)
            subprocess.run(f"chown -R {celery_user}:{celery_user} {postgres_cert_dir}", shell=True, check=True)
            
            # Make root's directory usable too
            root_cert_dir = "/root/.postgresql"
            os.makedirs(root_cert_dir, exist_ok=True)
            shutil.copy(f"{ssl_src_dir}/transcendence.crt", f"{root_cert_dir}/postgresql.crt")
            shutil.copy(f"{ssl_src_dir}/transcendence.key", f"{root_cert_dir}/postgresql.key")
            subprocess.run(f"chmod 644 {root_cert_dir}/postgresql.crt", shell=True, check=True)
            subprocess.run(f"chmod 644 {root_cert_dir}/postgresql.key", shell=True, check=True)
            subprocess.run(f"chmod -R 755 /root/.postgresql", shell=True, check=True)
            
            logger.info(f"PostgreSQL certificates copied to both {postgres_cert_dir} and {root_cert_dir}")
            return True
        else:
            logger.warning("SSL certificates not found for PostgreSQL")
            return False
    except Exception as e:
        logger.error(f"Error setting up SSL certificates: {e}")
        return False

def create_pg_service_file(celery_user=None):
    """Create PostgreSQL service file for Celery"""
    if not celery_user:
        celery_user = os.environ.get("CELERY_USER")
        if not celery_user:
            logger.warning("CELERY_USER environment variable not set, using fallback 'celeryuser'")
            celery_user = "celeryuser"
    
    try:
        # Get database configuration from environment
        db_host = os.environ.get("SQL_HOST")
        if not db_host:
            logger.warning("SQL_HOST environment variable not set, using fallback 'db'")
            db_host = "db"
        
        db_port = os.environ.get("SQL_PORT")
        if not db_port:
            logger.warning("SQL_PORT environment variable not set, using fallback '5432'")
            db_port = "5432"
        
        db_user = os.environ.get("POSTGRES_USER")
        if not db_user:
            logger.warning("POSTGRES_USER environment variable not set, using fallback 'postgres'")
            db_user = "postgres"
        
        db_password = os.environ.get("POSTGRES_PASSWORD", "")
        db_name = os.environ.get("POSTGRES_DB")
        if not db_name:
            logger.warning("POSTGRES_DB environment variable not set, using fallback 'postgres'")
            db_name = "postgres"
        
        # Get SSL configuration
        ssl_mode = os.environ.get("CELERY_PGSSLMODE", "require")
        ssl_cert = os.environ.get("CELERY_PGSSLCERT", f"/home/{celery_user}/.postgresql/postgresql.crt")
        ssl_key = os.environ.get("CELERY_PGSSLKEY", f"/home/{celery_user}/.postgresql/postgresql.key")
        
        # Create a custom config file to avoid SSL certificate path issues
        pg_config_dir = f"/home/{celery_user}/.pg"
        os.makedirs(pg_config_dir, exist_ok=True)
        pg_service_file = f"{pg_config_dir}/pg_service.conf"
        
        with open(pg_service_file, 'w') as f:
            f.write("[celery_service]\n")
            f.write(f"host={db_host}\n")
            f.write(f"port={db_port}\n")
            f.write(f"user={db_user}\n")
            f.write(f"password={db_password}\n")
            f.write(f"dbname={db_name}\n")
            f.write(f"sslmode={ssl_mode}\n")
            f.write(f"sslcert={ssl_cert}\n")
            f.write(f"sslkey={ssl_key}\n")
        
        subprocess.run(f"chown -R {celery_user}:{celery_user} {pg_config_dir}", shell=True, check=True)
        subprocess.run(f"chmod 600 {pg_service_file}", shell=True, check=True)
        
        logger.info(f"Created PostgreSQL service file at {pg_service_file}")
        return pg_service_file
        
    except Exception as e:
        logger.error(f"Error creating PostgreSQL service file: {e}")
        return None

def get_worker_command(celery_user=None):
    """Get command to start Celery worker"""
    if not celery_user:
        celery_user = os.environ.get("CELERY_USER")
        if not celery_user:
            logger.warning("CELERY_USER environment variable not set, using fallback 'celeryuser'")
            celery_user = "celeryuser"
    
    # Get database configuration
    db_host = os.environ.get("SQL_HOST", "db")
    db_port = os.environ.get("SQL_PORT", "5432")
    db_user = os.environ.get("POSTGRES_USER", "postgres")
    db_password = os.environ.get("POSTGRES_PASSWORD", "")
    db_name = os.environ.get("POSTGRES_DB", "postgres")
    
    # Get SSL configuration
    ssl_mode = os.environ.get("CELERY_PGSSLMODE", "require")
    ssl_cert = os.environ.get("CELERY_PGSSLCERT", f"/home/{celery_user}/.postgresql/postgresql.crt")
    ssl_key = os.environ.get("CELERY_PGSSLKEY", f"/home/{celery_user}/.postgresql/postgresql.key")
    
    # Create service file path
    pg_service_file = f"/home/{celery_user}/.pg/pg_service.conf"
    
    # Environment variables
    env_vars = (
        f"PGHOST={db_host} "
        f"PGPORT={db_port} "
        f"PGUSER={db_user} "
        f"PGPASSWORD={db_password} "
        f"PGDATABASE={db_name} "
        f"PGSSLMODE={ssl_mode} "
        f"PGSSLCERT={ssl_cert} "
        f"PGSSLKEY={ssl_key} "
        f"PGSSLROOTCERT={ssl_cert} "
        f"PGSERVICEFILE={pg_service_file} "
        f"PGSERVICE=celery_service "
    )
    
    # Command to start worker
    worker_cmd = (
        f"su -m {celery_user} -c '"
        f"{env_vars} "
        f"celery -A main worker --loglevel=info'"
    )
    
    return worker_cmd

def get_beat_command(celery_user=None):
    """Get command to start Celery beat"""
    if not celery_user:
        celery_user = os.environ.get("CELERY_USER")
        if not celery_user:
            logger.warning("CELERY_USER environment variable not set, using fallback 'celeryuser'")
            celery_user = "celeryuser"
    
    # Get database configuration
    db_host = os.environ.get("SQL_HOST", "db")
    db_port = os.environ.get("SQL_PORT", "5432")
    db_user = os.environ.get("POSTGRES_USER", "postgres")
    db_password = os.environ.get("POSTGRES_PASSWORD", "")
    db_name = os.environ.get("POSTGRES_DB", "postgres")
    
    # Get SSL configuration
    ssl_mode = os.environ.get("CELERY_PGSSLMODE", "require")
    ssl_cert = os.environ.get("CELERY_PGSSLCERT", f"/home/{celery_user}/.postgresql/postgresql.crt")
    ssl_key = os.environ.get("CELERY_PGSSLKEY", f"/home/{celery_user}/.postgresql/postgresql.key")
    
    # Create service file path
    pg_service_file = f"/home/{celery_user}/.pg/pg_service.conf"
    beat_schedule = os.environ.get("CELERYBEAT_SCHEDULE_FILENAME", f"/var/lib/celery/celerybeat-schedule")
    
    # Environment variables
    env_vars = (
        f"PGHOST={db_host} "
        f"PGPORT={db_port} "
        f"PGUSER={db_user} "
        f"PGPASSWORD={db_password} "
        f"PGDATABASE={db_name} "
        f"PGSSLMODE={ssl_mode} "
        f"PGSSLCERT={ssl_cert} "
        f"PGSSLKEY={ssl_key} "
        f"PGSSLROOTCERT={ssl_cert} "
        f"PGSERVICEFILE={pg_service_file} "
        f"PGSERVICE=celery_service "
    )
    
    # Command to start beat
    beat_cmd = (
        f"su -m {celery_user} -c '"
        f"{env_vars} "
        f"celery -A main beat --loglevel=info --schedule={beat_schedule}'"
    )
    
    return beat_cmd

def setup_celery():
    """Complete Celery setup process"""
    celery_user = os.environ.get("CELERY_USER")
    if not celery_user:
        logger.warning("CELERY_USER environment variable not set, using fallback 'celeryuser'")
        celery_user = "celeryuser"
    
    # Create directory for beat schedule
    os.makedirs("/var/lib/celery", exist_ok=True)
    subprocess.run(f"chown -R {celery_user}:{celery_user} /var/lib/celery", shell=True, check=True)
    
    # Export environment variable for Celery beat
    os.environ["CELERYBEAT_SCHEDULE_FILENAME"] = "/var/lib/celery/celerybeat-schedule"
    
    # Configure SSL certificates
    ssl_configured = configure_ssl_certificates(celery_user)
    
    # Create PostgreSQL service file
    pg_service_file = create_pg_service_file(celery_user)
    
    return ssl_configured and pg_service_file is not None

# Set up security, worker, and beat configurations
app.conf.update(**settings.CELERY_SECURITY_CONFIG)

# Worker configuration
app.conf.update(**settings.CELERY_WORKER_CONFIG)

# Apply the configuration for the beat
app.conf.update(**settings.CELERY_BEAT_CONFIG)

# Get PostgreSQL SSL settings from environment (loaded from Vault)
pg_ssl_mode = os.environ.get('CELERY_PGSSLMODE', 'require')
pg_app_name = os.environ.get('CELERY_PGAPPNAME', 'celery_worker')
pg_ssl_cert = os.environ.get('CELERY_PGSSLCERT', '')
pg_ssl_key = os.environ.get('CELERY_PGSSLKEY', '')

# Configure SSL settings for PostgreSQL connection
# Set the SSL connection parameters as environment variables for Celery workers
os.environ.setdefault('PGSSLMODE', pg_ssl_mode)
os.environ.setdefault('PGAPPNAME', pg_app_name)
os.environ.setdefault('PGSSLCERT', pg_ssl_cert)
os.environ.setdefault('PGSSLKEY', pg_ssl_key)

# Update Celery configuration with PostgreSQL options
app.conf.update(
    broker_connection_retry_on_startup=True,
    worker_enable_remote_control=False,
    worker_send_task_events=False,
    task_send_sent_event=False,
    worker_log_format='[%(asctime)s: %(levelname)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s] %(task_name)s - %(message)s',
    worker_redirect_stdouts_level='ERROR',
    database_engine_options={
        'sslmode': pg_ssl_mode,
        'application_name': pg_app_name,
        'connect_timeout': 30,
    }
)

# Search for tasks in Django applications
app.autodiscover_tasks()

@app.task(bind=True) # app.task decorator to create a task from a regular function
def debug_task(self):
    print(f'Request: {self.request!r}')
