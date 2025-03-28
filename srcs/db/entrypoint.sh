#!/bin/bash

set -e # Exit on error

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Function to print formatted messages
log() {
  local level=$1 # INFO, WARN, ERROR
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

# Copy certificates from shared location to PostgreSQL directory
copy_certs_to_postgres() {
  log "INFO" "Copying certificates to PostgreSQL directory..."
  
  mkdir -p /var/lib/postgresql/ssl
  chmod 755 /var/lib/postgresql/ssl
  
  if [ -f "/tmp/ssl/transcendence.crt" ] && [ -f "/tmp/ssl/transcendence.key" ]; then
    cp /tmp/ssl/transcendence.crt /var/lib/postgresql/ssl/server.crt
    cp /tmp/ssl/transcendence.key /var/lib/postgresql/ssl/server.key
    chmod 644 /var/lib/postgresql/ssl/server.crt
    chmod 600 /var/lib/postgresql/ssl/server.key
    chown postgres:postgres /var/lib/postgresql/ssl/server.crt
    chown postgres:postgres /var/lib/postgresql/ssl/server.key
    log "INFO" "✅ Certificates copied successfully"
    return 0
  else
    log "ERROR" "Required certificates not found in /tmp/ssl"
    return 1
  fi
}

# Wait for Vault to be ready
log "INFO" "Loading credentials from Vault..."
echo "⏳ Starting Vault secrets initialization..."

# Wait for Vault to be initialized and token to be available with progressive backoff
wait_for_vault() {
    echo "Waiting for Vault to be ready..."
    max_attempts=20
    attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        # Calculate wait time with progressive backoff (starts at 2s, caps at 10s)
        wait_time=$(( 2 * (attempt < 5 ? attempt : 5) ))
        
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
        
        echo "⏳ Attempt $attempt of $max_attempts - Vault is unavailable, waiting ${wait_time}s..."
        attempt=$((attempt + 1))
        sleep $wait_time
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

# Fix certificate permissions and copy to PostgreSQL directory (persistent volume)
if ! copy_certs_to_postgres; then
  log "ERROR" "Failed to copy certificates"
  exit 1
fi

# Start PostgreSQL
log "INFO" "Starting PostgreSQL..."
exec docker-entrypoint.sh postgres
