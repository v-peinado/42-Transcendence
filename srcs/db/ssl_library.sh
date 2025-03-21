#!/bin/bash

# PostgreSQL SSL Configuration Library
# This library provides common functions for SSL certificate management
# and PostgreSQL SSL configuration.

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# -----------------------------------------------------------
# Logging Functions
# -----------------------------------------------------------

# Format and print log messages with appropriate colors
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

# Log a section header for better readability
log_section() {
  local title=$1
  log "INFO" "=============================================="
  log "INFO" "$title"
  log "INFO" "=============================================="
}

# -----------------------------------------------------------
# SSL Certificate Management
# -----------------------------------------------------------

# Configure permissions for SSL certificates and keys
configure_cert_permissions() {
  log_section "Configuring SSL certificate permissions"

  # Locations where certificates might be stored
  local cert_locations=(
    "/tmp/ssl"
    "/var/lib/postgresql/ssl"
  )

  # Process each location
  for location in "${cert_locations[@]}"; do
    if [ -d "$location" ]; then
      log "INFO" "Checking certificates in $location..."
      
      # Process certificate files
      for cert in "$location"/*.crt; do
        if [ -f "$cert" ]; then
          log "INFO" "Setting permissions for $cert"
          chmod 644 "$cert" || log "WARN" "Failed to set permissions for $cert"
          
          if [ "$(id -u)" = "0" ]; then
            if [[ "$cert" == "/var/lib/postgresql"* ]]; then
              chown postgres:postgres "$cert" || log "WARN" "Failed to change ownership of $cert"
            fi
          fi
          
          if [ -f "$cert" ]; then
            log "INFO" "✅ Updated permissions: $(stat -c "%a %U:%G" "$cert")"
          fi
        fi
      done
      
      # Process key files
      for key in "$location"/*.key; do
        if [ -f "$key" ]; then
          log "INFO" "Setting permissions for $key"
          
          if [[ "$key" == "/var/lib/postgresql"* ]]; then
            chmod 600 "$key" || log "WARN" "Failed to set permissions for $key"
            if [ "$(id -u)" = "0" ]; then
              chown postgres:postgres "$key" || log "WARN" "Failed to change ownership of $key"
            fi
          else
            log "WARN" "Setting permissions for shared key (development only)"
            
            if getent group ssl-cert > /dev/null; then
              chown root:ssl-cert "$key" || log "WARN" "Failed to change ownership of $key"
              chmod 640 "$key" || log "WARN" "Failed to set permissions for $key"
            else
              log "WARN" "ssl-cert group not found, setting minimum permissions"
              chmod 644 "$key" || log "WARN" "Failed to set permissions for $key"
            fi
          fi
          
          if [ -f "$key" ]; then
            log "INFO" "✅ Updated permissions: $(stat -c "%a %U:%G" "$key")"
          fi
        fi
      done
    else
      log "WARN" "Directory $location does not exist"
    fi
  done

  log "INFO" "Certificate permission configuration completed"
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

# -----------------------------------------------------------
# PostgreSQL Configuration
# -----------------------------------------------------------

# Configure SSL settings in postgresql.conf
configure_postgresql_ssl() {
  log "INFO" "Configuring SSL in postgresql.conf..."
  
  if [ ! -f "${PGDATA}/postgresql.conf" ]; then
    log "ERROR" "postgresql.conf not found"
    return 1
  fi
  
  # Create backup
  cp -f "${PGDATA}/postgresql.conf" "${PGDATA}/postgresql.conf.bak.$(date +%s)"
  
  # Remove any existing SSL configuration
  sed -i '/^ssl.*=/d' "${PGDATA}/postgresql.conf"
  sed -i '/SSL Configuration/d' "${PGDATA}/postgresql.conf"
  sed -i '/^log_connections/d' "${PGDATA}/postgresql.conf"
  
  # Add clean SSL configuration
  cat >> "${PGDATA}/postgresql.conf" << EOF

# SSL Configuration - Added $(date)
ssl = on
ssl_cert_file = '/var/lib/postgresql/ssl/server.crt'
ssl_key_file = '/var/lib/postgresql/ssl/server.key'
ssl_ca_file = '/var/lib/postgresql/ssl/server.crt'

# SSL Protocol settings
ssl_min_protocol_version = 'TLSv1.2'
ssl_max_protocol_version = 'TLSv1.3'
ssl_prefer_server_ciphers = off

# Compatible ciphers
ssl_ciphers = 'HIGH:MEDIUM:+3DES:!aNULL'

# Monitoring
log_connections = on
EOF

  log "INFO" "SSL configuration added to postgresql.conf"
}

# Configure pg_hba.conf for SSL connections
configure_pghba_ssl() {
  log "INFO" "Configuring pg_hba.conf for SSL connections..."
  
  if [ ! -f "${PGDATA}/pg_hba.conf" ]; then
    log "ERROR" "pg_hba.conf not found"
    return 1
  fi
  
  # Add Docker container network rule if not exists
  if ! grep -q "^hostssl.*all.*all.*172\." "${PGDATA}/pg_hba.conf"; then
    log "INFO" "Adding SSL rule for Docker networks..."
    echo "hostssl all             all             172.0.0.0/8            md5" >> "${PGDATA}/pg_hba.conf"
    echo "hostssl all             all             all                    md5" >> "${PGDATA}/pg_hba.conf"
  fi
  
  log "INFO" "pg_hba.conf configured for SSL"
}

# -----------------------------------------------------------
# Connection Testing
# -----------------------------------------------------------

# Test PostgreSQL SSL connection
test_ssl_connection() {
  if ! pg_isready -q; then
    log "ERROR" "PostgreSQL is not running"
    return 1
  fi
  
  log "INFO" "Testing SSL connection..."
  if PGSSLMODE=require psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -h localhost -c "SELECT 'SSL connection successful';" > /dev/null 2>&1; then
    log "INFO" "✅ SSL connection test successful"
    return 0
  else
    log "ERROR" "❌ SSL connection test failed"
    return 1
  fi
}

# Check for active SSL connections
check_ssl_connections() {
  log_section "Checking active SSL connections"
  
  if ! pg_isready -q; then
    log "ERROR" "PostgreSQL is not running"
    return 1
  fi
  
  # Get PostgreSQL version
  local pg_version=$(psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SHOW server_version;" 2>/dev/null | xargs)
  log "INFO" "PostgreSQL version: $pg_version"
  
  # Show SSL status
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SHOW ssl;" 2>/dev/null
  
  # Count SSL vs non-SSL connections
  log "INFO" "Connection summary:"
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
  SELECT 
      ssl AS ssl_active,
      COUNT(*) as connections
  FROM 
      pg_stat_ssl 
  JOIN 
      pg_stat_activity ON pg_stat_ssl.pid = pg_stat_activity.pid 
  WHERE 
      pg_stat_activity.backend_type = 'client backend'
  GROUP BY 
      ssl
  ORDER BY 
      ssl DESC;
  " 2>/dev/null
  
  # Check for Django connections with SSL
  log "INFO" "Checking for Django SSL connections..."
  local django_ssl_count=$(psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "
  SELECT COUNT(*) 
  FROM pg_stat_ssl ssl
  JOIN pg_stat_activity sa ON ssl.pid = sa.pid
  WHERE host(sa.client_addr) ~ '^172\.' 
    AND ssl.ssl = 't'
    AND sa.application_name LIKE 'django%';
  " 2>/dev/null | tr -d '[:space:]')
  
  if [ "$django_ssl_count" = "0" ] || [ -z "$django_ssl_count" ]; then
    log "WARN" "No SSL connections from Django detected"
  else
    log "INFO" "✅ $django_ssl_count active SSL connections from Django"
  fi
  
  log "INFO" "SSL connection check completed"
}
