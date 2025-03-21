#!/bin/bash

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

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

# Source environment variables
if [ -f "/tmp/ssl/db.env" ]; then
  source /tmp/ssl/db.env
else
  log "ERROR" "Environment file not found"
  exit 1
fi

# Verify SSL connection to PostgreSQL
verify_ssl_connection() {
  log "INFO" "Verifying SSL connection to PostgreSQL..."
  
  # Use psql to check if SSL is being used
  if PGSSLMODE=require PGPASSWORD="$POSTGRES_PASSWORD" psql -h localhost -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT ssl, version FROM pg_stat_ssl JOIN pg_stat_activity ON pg_stat_ssl.pid = pg_stat_activity.pid WHERE pg_stat_activity.backend_type = 'client backend' LIMIT 1;" 2>/dev/null | grep -q "t"; then
    log "INFO" "PostgreSQL is correctly configured with SSL"
    
    # Get more detailed SSL information
    ssl_info=$(PGSSLMODE=require PGPASSWORD="$POSTGRES_PASSWORD" psql -h localhost -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT ssl_version, ssl_cipher FROM pg_stat_ssl JOIN pg_stat_activity ON pg_stat_ssl.pid = pg_stat_activity.pid WHERE pg_stat_activity.backend_type = 'client backend' LIMIT 1;" -t 2>/dev/null)
    
    log "INFO" "SSL Version: $(echo "$ssl_info" | awk '{print $1}')"
    log "INFO" "SSL Cipher: $(echo "$ssl_info" | awk '{print $2}')"
    return 0
  else
    log "ERROR" "PostgreSQL is NOT using SSL"
    return 1
  fi
}

# Verify certificates
verify_certificates() {
  log "INFO" "Verifying SSL certificates..."
  
  if [ ! -f "/tmp/ssl/transcendence.crt" ]; then
    log "ERROR" "Certificate file not found"
    return 1
  fi
  
  if [ ! -f "/tmp/ssl/transcendence.key" ]; then
    log "ERROR" "Key file not found"
    return 1
  }
  
  # Verify certificate is valid
  if ! openssl x509 -in /tmp/ssl/transcendence.crt -noout -text >/dev/null 2>&1; then
    log "ERROR" "Certificate is not valid"
    return 1
  fi
  
  log "INFO" "SSL certificates are valid"
  return 0
}

# Main function
main() {
  log "INFO" "Starting SSL verification..."
  
  if ! verify_certificates; then
    log "ERROR" "Certificate verification failed"
    exit 1
  fi
  
  if ! verify_ssl_connection; then
    log "ERROR" "SSL connection verification failed"
    exit 1
  fi
  
  log "INFO" "All SSL verifications passed successfully!"
}

main "$@"
