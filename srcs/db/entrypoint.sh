#!/bin/bash

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Function to print formatted messages
log() {
  local level=$1
  local message=$2
  
  case $level in
    "INFO")
      echo -e "${GREEN}[INFO]${NC} $message"
      ;;
    "WARN")
      echo -e "${YELLOW}[WARN]${NC} $message"
      ;;
    "ERROR")
      echo -e "${RED}[ERROR]${NC} $message" >&2
      ;;
    *)
      echo -e "$message"
      ;;
  esac
}

# Source the SSL library functions
if [ -f "/usr/local/bin/ssl_library.sh" ]; then
  source /usr/local/bin/ssl_library.sh
else
  echo "ERROR: SSL library not found"
  exit 1
fi

# Wait for Vault to be ready
log "INFO" "Loading credentials from Vault..."
echo "⏳ Starting Vault secrets initialization..."

# Wait for Vault to be initialized and token to be available
wait_for_vault() {
    echo "Waiting for Vault to be ready..."
    max_attempts=45
    attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        # Check if token file exists
        if [ -f "/tmp/ssl/django_token" ]; then
            token=$(cat /tmp/ssl/django_token)
            if [ -n "$token" ]; then
                # Verify we can connect to Vault
                if curl -s -k -H "X-Vault-Token: $token" https://vault:8200/v1/sys/health > /dev/null; then
                    echo "✅ Vault is ready and token is available"
                    return 0
                fi
            fi
        fi
        
        echo "⏳ Attempt $attempt of $max_attempts - Vault is unavailable, sleeping..."
        attempt=$((attempt + 1))
        sleep 5
    done
    
    echo "❌ Error: Timeout waiting for Vault"
    return 1
}

# Call the function to wait for Vault
wait_for_vault

# Get secrets from Vault
/usr/local/bin/get-vault-secrets.sh

# Prepare PostgreSQL SSL directory and certificates
log "INFO" "Setting up SSL configuration..."
mkdir -p /var/lib/postgresql/ssl
chmod 755 /var/lib/postgresql/ssl
chown postgres:postgres /var/lib/postgresql/ssl

# Fix certificate permissions and copy to PostgreSQL directory
configure_cert_permissions > /dev/null 2>&1
if ! copy_certs_to_postgres; then
  log "ERROR" "Failed to copy certificates"
  exit 1
fi

# Configure PostgreSQL if data directory exists
if [ -f "${PGDATA}/postgresql.conf" ]; then
  configure_postgresql_ssl > /dev/null 2>&1
  configure_pghba_ssl > /dev/null 2>&1
fi

# Start PostgreSQL
log "INFO" "Starting PostgreSQL..."
exec docker-entrypoint.sh postgres
