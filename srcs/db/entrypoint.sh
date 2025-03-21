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

# Load credentials from Vault
log "INFO" "Loading credentials from Vault..."
/usr/local/bin/get-vault-secrets.sh

# Prepare PostgreSQL SSL directory
log "INFO" "Setting up SSL configuration..."
mkdir -p /var/lib/postgresql/ssl
chmod 755 /var/lib/postgresql/ssl
chown postgres:postgres /var/lib/postgresql/ssl

# Fix certificate permissions
configure_cert_permissions

# Copy certificates to PostgreSQL directory
if ! copy_certs_to_postgres; then
  log "ERROR" "Failed to copy certificates"
  exit 1
fi

# Configure PostgreSQL if data directory exists
if [ -f "${PGDATA}/postgresql.conf" ]; then
  # Configure SSL in postgresql.conf
  configure_postgresql_ssl
  
  # Configure pg_hba.conf for SSL connections
  configure_pghba_ssl
fi

# Start PostgreSQL
log "INFO" "Starting PostgreSQL..."
exec docker-entrypoint.sh postgres
