#!/bin/bash

set -e

# Colores para salida
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Imprimir mensajes formateados
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

# Función para reparar el archivo postgresql.conf
repair_config() {
  local config_file="${PGDATA}/postgresql.conf"
  
  if [ ! -f "$config_file" ]; then
    log "ERROR" "No se encontró el archivo de configuración en $config_file"
    return 1
  fi
  
  log "INFO" "Creando copia de seguridad de postgresql.conf..."
  cp "$config_file" "${config_file}.$(date +%Y%m%d%H%M%S).bak"
  
  log "INFO" "Limpiando configuraciones SSL existentes..."
  # Eliminar cualquier configuración SSL que podría estar malformada
  sed -i '/^ssl[^=]*=[^=]*=[^=]*/d' "$config_file"
  sed -i '/^ssl.*=.*=.*/d' "$config_file"
  
  # Eliminar configuración SSL existente para evitar duplicados
  sed -i '/^ssl =/d' "$config_file"
  sed -i '/^ssl_cert_file =/d' "$config_file"
  sed -i '/^ssl_key_file =/d' "$config_file"
  sed -i '/^ssl_ca_file =/d' "$config_file"
  sed -i '/^ssl_ciphers =/d' "$config_file"
  sed -i '/^log_connections =/d' "$config_file"
  
  log "INFO" "Agregando nueva configuración SSL limpia..."
  # Agregar configuración SSL limpia al final del archivo
  cat >> "$config_file" <<EOF

# SSL Configuration - Repaired $(date)
ssl = on
ssl_cert_file = '/var/lib/postgresql/ssl/server.crt'
ssl_key_file = '/var/lib/postgresql/ssl/server.key'
ssl_ca_file = '/var/lib/postgresql/ssl/server.crt'
ssl_ciphers = 'HIGH:MEDIUM:+3DES:!aNULL'
log_connections = on
EOF
  
  log "INFO" "Validando archivo de configuración..."
  # Verificar sintaxis
  if ! postgres -C "config_file=$config_file" 2>/dev/null; then
    log "ERROR" "El archivo de configuración tiene errores de sintaxis"
    return 1
  fi
  
  log "INFO" "Configuración reparada exitosamente"
  return 0
}

# Verificar que estamos ejecutando como postgres
if [ "$(whoami)" != "postgres" ] && [ "$(whoami)" != "root" ]; then
  log "ERROR" "Este script debe ser ejecutado como usuario postgres o root"
  exit 1
fi

# Verificar que PGDATA está establecido
if [ -z "$PGDATA" ]; then
  PGDATA="/var/lib/postgresql/data"
  log "WARN" "PGDATA no establecido, usando valor por defecto: $PGDATA"
fi

log "INFO" "Iniciando reparación de la configuración de PostgreSQL..."
if repair_config; then
  log "INFO" "Reparación completada. Reinicie PostgreSQL para aplicar los cambios."
  log "INFO" "Puede reiniciar con: pg_ctl -D $PGDATA restart"
else
  log "ERROR" "No se pudo reparar la configuración"
  exit 1
fi

exit 0
