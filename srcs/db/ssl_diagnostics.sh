#!/bin/bash

# PostgreSQL SSL Diagnostics Script
# This script checks the SSL configuration and connections for PostgreSQL

# Source the SSL library functions
if [ -f "/usr/local/bin/ssl_library.sh" ]; then
  source /usr/local/bin/ssl_library.sh
else
  echo "ERROR: SSL library not found"
  exit 1
fi

# Run a full SSL diagnostic
run_ssl_diagnostics() {
  log_section "Running PostgreSQL SSL Diagnostics"
  
  # Check if PostgreSQL is running
  if ! pg_isready -q; then
    log "ERROR" "PostgreSQL is not running"
    exit 1
  fi
  
  # Check SSL configuration in PostgreSQL
  log "INFO" "PostgreSQL SSL configuration:"
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SHOW ssl;" || log "ERROR" "Failed to check SSL status"
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SHOW ssl_cert_file;" || log "ERROR" "Failed to check SSL certificate"
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SHOW ssl_key_file;" || log "ERROR" "Failed to check SSL key"
  
  # Verify certificate files
  log "INFO" "Checking certificate files..."
  local cert_file=$(psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SHOW ssl_cert_file;" | xargs)
  local key_file=$(psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SHOW ssl_key_file;" | xargs)
  
  [ -f "$cert_file" ] && log "INFO" "✅ Certificate file exists: $cert_file" || log "ERROR" "❌ Certificate file missing: $cert_file"
  [ -f "$key_file" ] && log "INFO" "✅ Key file exists: $key_file" || log "ERROR" "❌ Key file missing: $key_file"
  
  # Check permissions
  if [ -f "$cert_file" ]; then
    log "INFO" "Certificate permissions: $(stat -c "%a %U:%G" "$cert_file")"
  fi
  
  if [ -f "$key_file" ]; then
    log "INFO" "Key permissions: $(stat -c "%a %U:%G" "$key_file")"
  fi
  
  # Check active connections
  check_ssl_connections
  
  # Test SSL connection
  test_ssl_connection
  
  log "INFO" "Diagnostics completed"
}

# Main execution
run_ssl_diagnostics
