# Environment variables needed for the project
# Copy this file as .env and fill in the values

# PostgreSQL Configuration
SQL_ENGINE=django.db.backends.postgresql    # Database engine
POSTGRES_DB=transcendence                   # Database name
POSTGRES_USER=usuario                       # PostgreSQL user
POSTGRES_PASSWORD=contraseña               # PostgreSQL password
SQL_HOST=db                                # Database host
SQL_PORT=5432                              # PostgreSQL port

# Django Configuration
DJANGO_SECRET_KEY=your-secret-key-here     # Django secret key (must be unique)
DJANGO_ALLOWED_HOSTS=localhost             # Allowed hosts, comma separated

# 42 Authentication
# Get these credentials at https://profile.intra.42.fr/oauth/applications
FORTYTWO_CLIENT_ID=your-client-id          # 42 OAuth client ID
FORTYTWO_CLIENT_SECRET=your-client-secret  # 42 OAuth client secret
FORTYTWO_REDIRECT_URI=https://localhost:8445/login/  # OAuth redirect URI

# 42 API
FORTYTWO_API_UID=your-api-uid              # 42 API UID
FORTYTWO_API_SECRET=your-api-secret        # 42 API secret
FORTYTWO_API_URL=your-api-url              # 42 API base URL

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
JWT_EXPIRATION_TIME=3600                   # Expiration time in seconds

# Vault Configuration (development only)
VAULT_ROOT_TOKEN=your-vault-token          # Vault root token
#VAULT_LOG_TOKENS=true                     # Enable token logs (development only)

