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
log "INFO" "Solucionando problemas SSL EOF en PostgreSQL"
log "INFO" "=============================================="

# 1. Verificar que los certificados existan y tengan los permisos correctos
log "INFO" "Verificando certificados y permisos..."

# Asegurar que los certificados sean accesibles
mkdir -p /var/lib/postgresql/ssl
cp /tmp/ssl/transcendence.crt /var/lib/postgresql/ssl/server.crt
cp /tmp/ssl/transcendence.key /var/lib/postgresql/ssl/server.key
chmod 644 /var/lib/postgresql/ssl/server.crt
chmod 600 /var/lib/postgresql/ssl/server.key
chown postgres:postgres /var/lib/postgresql/ssl/server.crt /var/lib/postgresql/ssl/server.key

log "INFO" "Certificados copiados y con permisos correctos"

# 2. Modificar el archivo postgresql.conf 
log "INFO" "Actualizando configuración SSL en PostgreSQL..."

# Hacer una copia de seguridad del archivo
cp "${PGDATA}/postgresql.conf" "${PGDATA}/postgresql.conf.bak-$(date +%s)"

# Remover todas las configuraciones SSL anteriores
sed -i '/^ssl[_=]/d' "${PGDATA}/postgresql.conf"

# Añadir la configuración actualizada
cat >> "${PGDATA}/postgresql.conf" << EOF

# SSL Configuration - Updated for EOF error fix ($(date))
ssl = on
ssl_cert_file = '/var/lib/postgresql/ssl/server.crt'
ssl_key_file = '/var/lib/postgresql/ssl/server.key'
ssl_ca_file = '/var/lib/postgresql/ssl/server.crt'
ssl_min_protocol_version = 'TLSv1.2'
ssl_max_protocol_version = 'TLSv1.3'
ssl_prefer_server_ciphers = off
ssl_ciphers = 'HIGH:!aNULL:!eNULL:!PSK:!RC4:!MD5:@STRENGTH'
ssl_ecdh_curve = 'prime256v1'
log_connections = on
EOF

log "INFO" "Configuración SSL actualizada"

# 3. Aplicar cambios en el entorno para admitir TLS 1.2
log "INFO" "Configurando variables de entorno para compatibilidad TLS..."

# Configurar variables que podrían afectar la compatibilidad TLS
export OPENSSL_CONF="${PGDATA}/openssl.cnf"
cat > "${PGDATA}/openssl.cnf" << EOF
openssl_conf = default_conf

[default_conf]
ssl_conf = ssl_sect

[ssl_sect]
system_default = system_default_sect

[system_default_sect]
MinProtocol = TLSv1.2
CipherString = HIGH:!aNULL:!eNULL:!PSK:!RC4:!MD5:@STRENGTH
EOF

log "INFO" "Variables de entorno configuradas"

# 4. Recargar configuración de PostgreSQL
log "INFO" "Recargando configuración de PostgreSQL..."
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT pg_reload_conf();"

# 5. Intenta una conexión SSL para verificar
log "INFO" "Verificando conexión SSL..."
if PGSSLMODE=require psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -h localhost -c "SELECT 'Conexión SSL exitosa';" 2>/dev/null; then
  log "INFO" "✅ Prueba de conexión SSL exitosa"
else
  log "ERROR" "❌ Prueba de conexión SSL fallida"
fi

log "INFO" "=============================================="
log "INFO" "Reparación completada"
log "INFO" "=============================================="

log "WARN" "Es posible que necesites reiniciar el contenedor de Django para aplicar cambios"
log "INFO" "Puedes probar si Django se conecta correctamente con SSL usando:"
log "INFO" "  docker exec -it \$(docker ps -q -f name=db) /usr/local/bin/check-ssl-from-django.sh"
