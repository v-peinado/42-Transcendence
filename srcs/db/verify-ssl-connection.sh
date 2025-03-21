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

# Verify SSL connection to PostgreSQL
verify_ssl_connection() {
  log "INFO" "Verifying SSL connection to PostgreSQL..."
  
  # Check permissions on SSL files
  log "INFO" "Checking certificate permissions:"
  ls -la /tmp/ssl/

  # Use psql to check if SSL is being used
  if PGSSLMODE=require psql -h localhost -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SHOW ssl;" 2>/dev/null | grep -q "on"; then
    log "INFO" "PostgreSQL SSL is enabled"
    
    # Get more detailed SSL information
    log "INFO" "Checking active SSL connections:"
    PGSSLMODE=require psql -h localhost -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
      -c "SELECT datname, usename, ssl, version, cipher, client_addr, client_port FROM pg_stat_ssl JOIN pg_stat_activity ON pg_stat_ssl.pid = pg_stat_activity.pid WHERE pg_stat_activity.backend_type = 'client backend';"
    
    log "INFO" "PostgreSQL SSL settings:"
    PGSSLMODE=require psql -h localhost -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
      -c "SHOW ssl_ciphers; SHOW ssl_cert_file; SHOW ssl_key_file; SHOW ssl_ca_file;"
    
    return 0
  else
    log "ERROR" "PostgreSQL SSL is NOT enabled"
    return 1
  fi
}

# Check environment variables
check_environment() {
  log "INFO" "Checking environment variables..."
  
  if [ -z "$POSTGRES_USER" ] || [ -z "$POSTGRES_DB" ] || [ -z "$POSTGRES_PASSWORD" ]; then
    log "ERROR" "Required environment variables are missing: POSTGRES_USER, POSTGRES_DB, POSTGRES_PASSWORD"
    return 1
  fi
  
  log "INFO" "Environment variables are correctly set"
  return 0
}

# Main function
main() {
  log "INFO" "Starting PostgreSQL SSL verification..."
  
  if ! check_environment; then
    log "ERROR" "Environment check failed"
    exit 1
  fi
  
  if ! verify_ssl_connection; then
    log "ERROR" "SSL connection verification failed"
    exit 1
  fi
  
  log "INFO" "All SSL verifications passed successfully!"
}

# Source environment variables if needed
if [ -f "/tmp/ssl/db.env" ]; then
  source /tmp/ssl/db.env
fi

main "$@"
