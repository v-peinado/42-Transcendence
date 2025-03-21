#!/bin/bash

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Print formatted message
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

# Full diagnostic of PostgreSQL SSL setup
diagnose_postgres_ssl() {
  log "INFO" "=============================================="
  log "INFO" "PostgreSQL SSL Diagnostic Tool"
  log "INFO" "=============================================="
  
  # Check PostgreSQL is running
  if ! pg_isready -q; then
    log "ERROR" "PostgreSQL is not running"
    return 1
  fi
  log "INFO" "PostgreSQL is running"
  
  # Check SSL directory
  log "INFO" "Checking SSL directories:"
  ls -la /var/lib/postgresql/ssl/ || log "ERROR" "SSL directory not found"
  
  # Check certificate files
  log "INFO" "Checking certificate files:"
  if [ -f "/var/lib/postgresql/ssl/server.crt" ]; then
    log "INFO" "Certificate file exists"
    openssl x509 -in /var/lib/postgresql/ssl/server.crt -noout -text | grep "Subject:" || log "ERROR" "Invalid certificate"
  else
    log "ERROR" "Certificate file missing"
  fi
  
  if [ -f "/var/lib/postgresql/ssl/server.key" ]; then
    log "INFO" "Key file exists"
  else
    log "ERROR" "Key file missing"
  fi
  
  # Check PostgreSQL configuration
  log "INFO" "PostgreSQL SSL configuration:"
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SHOW ssl;"
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SHOW ssl_cert_file;"
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SHOW ssl_key_file;"
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SHOW ssl_ca_file;"
  
  # Test non-SSL connection
  log "INFO" "Testing standard connection:"
  PGPASSWORD="$POSTGRES_PASSWORD" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -h localhost -c "SELECT version();" && \
    log "INFO" "Standard connection works" || log "ERROR" "Standard connection failed"
  
  # Test SSL connection
  log "INFO" "Testing explicit SSL connection:"
  PGSSLMODE=require PGPASSWORD="$POSTGRES_PASSWORD" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -h localhost \
    -c "SELECT ssl, version FROM pg_stat_ssl JOIN pg_stat_activity ON pg_stat_ssl.pid = pg_stat_activity.pid WHERE pg_stat_activity.backend_type = 'client backend' LIMIT 1;" && \
    log "INFO" "SSL connection works" || log "ERROR" "SSL connection failed"
  
  # Check SSL connections in pg_stat_ssl
  log "INFO" "Current SSL connections:"
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT count(*) FROM pg_stat_ssl WHERE ssl = 't';"
  
  log "INFO" "=============================================="
  log "INFO" "Diagnostic complete"
}

# Main function
main() {
  # Source environment variables if available
  if [ -f "/tmp/ssl/db.env" ]; then
    source /tmp/ssl/db.env
  fi
  
  # Run diagnostics
  diagnose_postgres_ssl
}

main "$@"
