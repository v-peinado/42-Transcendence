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

# Cargar secrets desde Vault
log "INFO" "Cargando credenciales desde Vault..."
/usr/local/bin/get-vault-secrets.sh

# Preparar directorio para certificados SSL
log "INFO" "Configurando certificados SSL..."
mkdir -p /var/lib/postgresql/ssl
chmod 755 /var/lib/postgresql/ssl
chown postgres:postgres /var/lib/postgresql/ssl

# Configurar permisos de certificados
log "INFO" "Ajustando permisos de certificados..."
/usr/local/bin/fix-certificate-permissions.sh

# Copiar certificados a directorio de PostgreSQL
if [ -f "/tmp/ssl/transcendence.crt" ] && [ -f "/tmp/ssl/transcendence.key" ]; then
  log "INFO" "Copiando certificados a directorio de PostgreSQL..."
  cp /tmp/ssl/transcendence.crt /var/lib/postgresql/ssl/server.crt
  cp /tmp/ssl/transcendence.key /var/lib/postgresql/ssl/server.key
  chmod 644 /var/lib/postgresql/ssl/server.crt
  chmod 600 /var/lib/postgresql/ssl/server.key
  chown postgres:postgres /var/lib/postgresql/ssl/server.crt
  chown postgres:postgres /var/lib/postgresql/ssl/server.key
else
  log "ERROR" "No se encontraron certificados en /tmp/ssl"
  exit 1
fi

# Configuración de SSL en postgresql.conf
if [ -f "${PGDATA}/postgresql.conf" ]; then
  log "INFO" "Configurando SSL en postgresql.conf..."
  # Hacer backup
  cp -f "${PGDATA}/postgresql.conf" "${PGDATA}/postgresql.conf.bak"
  
  # Eliminar configuraciones SSL antiguas
  sed -i '/^ssl.*=/d' "${PGDATA}/postgresql.conf"
  sed -i '/SSL Configuration/d' "${PGDATA}/postgresql.conf"
  
  # Añadir nueva configuración
  cat >> "${PGDATA}/postgresql.conf" << EOF

# SSL Configuration - Added by entrypoint.sh $(date)
ssl = on
ssl_cert_file = '/var/lib/postgresql/ssl/server.crt'
ssl_key_file = '/var/lib/postgresql/ssl/server.key'
ssl_ca_file = '/var/lib/postgresql/ssl/server.crt'
ssl_ciphers = 'HIGH:MEDIUM:+3DES:!aNULL'
log_connections = on
EOF

  # Configuración de pg_hba.conf
  if [ -f "${PGDATA}/pg_hba.conf" ]; then
    log "INFO" "Verificando pg_hba.conf..."
    # Añadir regla para contenedores Docker si no existe
    if ! grep -q "^hostssl.*all.*all.*172\." "${PGDATA}/pg_hba.conf"; then
      log "INFO" "Añadiendo regla SSL para redes Docker..."
      echo "hostssl all             all             172.0.0.0/8            md5" >> "${PGDATA}/pg_hba.conf"
      echo "hostssl all             all             all                    md5" >> "${PGDATA}/pg_hba.conf"
    fi
  fi
fi

# Iniciar PostgreSQL
log "INFO" "Iniciando PostgreSQL..."
exec docker-entrypoint.sh postgres
