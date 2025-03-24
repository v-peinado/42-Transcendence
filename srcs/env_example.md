# Environment variables needed for the project
# Copy this file as .env and fill in the values

# PostgreSQL Configuration
SQL_ENGINE=django.db.backends.postgresql   # Database engine
POSTGRES_DB=transcendence                  # Database name
POSTGRES_USER=your_username                # PostgreSQL user
POSTGRES_PASSWORD=your_password            # PostgreSQL password
SQL_HOST=db                                # Database host
SQL_PORT=5432                              # PostgreSQL port

# Django Configuration
DJANGO_SECRET_KEY=your-secret-key-here     # Django secret key (must be unique)
DJANGO_ALLOWED_HOSTS=localhost             # Allowed hosts, comma separated

# GDPR Configuration
ENCRYPTION_KEY=your-32-bytes-base64-key    # GDPR Email Encryption Key (32 bytes base64-encoded)

# IP server 
IP_SERVER=                                 # execute ./configure_ip.sh

# 42 OAuth Web Application
FORTYTWO_CLIENT_ID=your-client-id          # 42 OAuth client ID
FORTYTWO_CLIENT_SECRET=your-client-secret  # 42 OAuth client secret
FORTYTWO_REDIRECT_URI=https://localhost:8445/login/  # OAuth redirect URI

# 42 API Configuration
FORTYTWO_API_UID=your-api-uid              # 42 API UID (same as client ID)
FORTYTWO_API_SECRET=your-api-secret        # 42 API secret (same as client secret)
FORTYTWO_API_URL=your-api-url              # 42 API redirect URL

# Email Configuration (SendGrid)
EMAIL_HOST=smtp.sendgrid.net               # SMTP host
EMAIL_PORT=587                             # SMTP port
EMAIL_USE_TLS=True                         # Use TLS for emails
EMAIL_HOST_USER=apikey                     # SMTP user (use 'apikey' for SendGrid)
EMAIL_HOST_PASSWORD=your-sendgrid-key      # SendGrid API key
DEFAULT_FROM_EMAIL=your@email.com          # Default sender email
SITE_URL=https://localhost:8443            # Site base URL

# JWT Configuration
JWT_SECRET_KEY=your-jwt-secret             # JWT secret key
JWT_ALGORITHM=HS256                        # JWT encryption algorithm
JWT_EXPIRATION_TIME=3600                   # Token expiration time in seconds

# Vault Configuration (development only)
#VAULT_ROOT_TOKEN=myroot                   # Vault root token (uncomment for development)
#VAULT_LOG_TOKENS=true                     # Enable token logs (development only)

# SSL Certificate Configuration
SSL_COUNTRY=ES                             # Country code (2 letters)
SSL_STATE=Madrid                           # State/Province
SSL_LOCALITY=Madrid                        # City/Locality
SSL_ORGANIZATION=42                        # Organization name
SSL_ORGANIZATIONAL_UNIT=42Madrid           # Organization unit
SSL_COMMON_NAME=localhost                  # Common Name (domain)
SSL_DAYS=365                               # Certificate validity in days
SSL_KEY_SIZE=2048                          # Key size in bits (min 2048)

# Celery Configuration
CELERY_USER=celeryuser                     # Celery user

# Celery PostgreSQL SSL Configuration
CELERY_PGSSLMODE=require                   # PostgreSQL SSL mode for Celery
CELERY_PGAPPNAME=celery_worker             # PostgreSQL application name for Celery
CELERY_PGSSLCERT=/home/celeryuser/.postgresql/postgresql.crt  # Path to PostgreSQL SSL certificate
CELERY_PGSSLKEY=/home/celeryuser/.postgresql/postgresql.key   # Path to PostgreSQL SSL key
