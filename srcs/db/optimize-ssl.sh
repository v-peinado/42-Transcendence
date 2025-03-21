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

log "INFO" "=============================================="
log "INFO" "Optimizando configuración SSL de PostgreSQL"
log "INFO" "=============================================="

# 1. Limpiar la configuración SSL en postgresql.conf
log "INFO" "Creando copia de seguridad de postgresql.conf..."
cp "${PGDATA}/postgresql.conf" "${PGDATA}/postgresql.conf.bak.$(date +%s)"

log "INFO" "Limpiando configuraciones SSL duplicadas o conflictivas..."
# Eliminar TODAS las configuraciones SSL existentes
sed -i '/^ssl.*=/d' "${PGDATA}/postgresql.conf"
sed -i '/SSL Configuration/d' "${PGDATA}/postgresql.conf"
sed -i '/^log_connections/d' "${PGDATA}/postgresql.conf"

# 2. Agregar una configuración SSL limpia y óptima
log "INFO" "Agregando configuración SSL optimizada..."
cat >> "${PGDATA}/postgresql.conf" << EOF

# SSL Configuration - Clean optimized configuration ($(date))
ssl = on
ssl_cert_file = '/var/lib/postgresql/ssl/server.crt'
ssl_key_file = '/var/lib/postgresql/ssl/server.key'
ssl_ca_file = '/var/lib/postgresql/ssl/server.crt'

# SSL Protocol settings
ssl_min_protocol_version = 'TLSv1.2'
ssl_max_protocol_version = 'TLSv1.3'
ssl_prefer_server_ciphers = off

# Compatible ciphers for Django
ssl_ciphers = 'HIGH:!aNULL:!eNULL:!PSK:!RC4:!MD5:+SHA1:@STRENGTH'

# Monitoring
log_connections = on
EOF

# 3. Verificar configuración de pg_hba.conf
log "INFO" "Verificando configuración de pg_hba.conf..."
if ! grep -q "^hostssl.*all.*all.*172\." "${PGDATA}/pg_hba.conf"; then
    log "WARN" "Agregando regla específica para contenedores Docker (172.x.x.x)..."
    sed -i '/hostssl all/d' "${PGDATA}/pg_hba.conf"
    echo "hostssl all             all             172.0.0.0/8            md5" >> "${PGDATA}/pg_hba.conf"
    echo "hostssl all             all             all                    md5" >> "${PGDATA}/pg_hba.conf"
fi

# 4. Copiar certificados y verificar permisos
log "INFO" "Actualizando certificados SSL..."
mkdir -p /var/lib/postgresql/ssl
if [ -f "/tmp/ssl/transcendence.crt" ] && [ -f "/tmp/ssl/transcendence.key" ]; then
    cp /tmp/ssl/transcendence.crt /var/lib/postgresql/ssl/server.crt
    cp /tmp/ssl/transcendence.key /var/lib/postgresql/ssl/server.key
    chmod 644 /var/lib/postgresql/ssl/server.crt
    chmod 600 /var/lib/postgresql/ssl/server.key
    chown postgres:postgres /var/lib/postgresql/ssl/server.crt /var/lib/postgresql/ssl/server.key
    log "INFO" "Certificados copiados y permisos establecidos correctamente"
else
    log "ERROR" "Certificados no encontrados en /tmp/ssl"
fi

# 5. Recargar la configuración de PostgreSQL
log "INFO" "Recargando configuración de PostgreSQL..."
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT pg_reload_conf();"

# 6. Verificar la configuración SSL
log "INFO" "Verificando configuración SSL..."
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SHOW ssl;"
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SHOW ssl_ciphers;"
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SHOW ssl_min_protocol_version;"

# 7. Probar conexión SSL local
log "INFO" "Probando conexión SSL local..."
if PGSSLMODE=require psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -h localhost -c "SELECT 'Conexión SSL exitosa';" > /dev/null 2>&1; then
    log "INFO" "✅ Conexión SSL local exitosa"
else
    log "ERROR" "❌ Conexión SSL local fallida"
fi

log "INFO" "=============================================="
log "INFO" "Optimización completada"
log "INFO" "=============================================="
