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
log "INFO" "Configurando permisos correctos para certificados SSL"
log "INFO" "=============================================="

# Ubicaciones de certificados
CERT_LOCATIONS=(
  "/tmp/ssl"
  "/var/lib/postgresql/ssl"
)

# Verificar y corregir permisos en todas las ubicaciones
for location in "${CERT_LOCATIONS[@]}"; do
  if [ -d "$location" ]; then
    log "INFO" "Verificando certificados en $location..."
    
    # Certificados
    for cert in "$location"/*.crt; do
      if [ -f "$cert" ]; then
        # Los certificados deben ser legibles pero no modificables excepto por el propietario
        log "INFO" "Configurando permisos para $cert"
        chmod 644 "$cert"
        # Asegurar propietario correcto si estamos como root
        if [ "$(id -u)" = "0" ]; then
          # Si el certificado está en /var/lib/postgresql, establecer postgres como propietario
          if [[ "$cert" == "/var/lib/postgresql"* ]]; then
            chown postgres:postgres "$cert"
          else
            # Para certificados en /tmp, permitir que los contenedores puedan leerlos
            chmod 644 "$cert"
          fi
        fi
        log "INFO" "✅ Permisos actualizados: $(stat -c "%a %U:%G" "$cert")"
      fi
    done
    
    # Claves privadas
    for key in "$location"/*.key; do
      if [ -f "$key" ]; then
        # Las claves privadas DEBEN ser muy restrictivas
        log "INFO" "Configurando permisos para $key"
        # Determinar los permisos según la ubicación y el propietario
        if [[ "$key" == "/var/lib/postgresql"* ]]; then
          # Para claves en PostgreSQL
          chmod 600 "$key"
          if [ "$(id -u)" = "0" ]; then
            chown postgres:postgres "$key"
          fi
        else
          # Para claves en /tmp/ssl que son accedidas por varios contenedores
          # Esto no es óptimo para producción pero facilita el desarrollo
          log "WARN" "Configurando permisos para clave compartida (solo para desarrollo)"
          chmod 600 "$key"
          # Si el grupo ssl-cert existe, usarlo para compartir claves
          if getent group ssl-cert > /dev/null; then
            chown root:ssl-cert "$key"
            chmod 640 "$key"  # Permitir lectura por el grupo pero no por otros
          else
            log "WARN" "Grupo ssl-cert no encontrado, configurando permisos mínimos"
            chmod 644 "$key"  # Solución temporal para desarrollo
          fi
        fi
        log "INFO" "✅ Permisos actualizados: $(stat -c "%a %U:%G" "$key")"
      fi
    done
  else
    log "WARN" "El directorio $location no existe"
  fi
done

# Ahora intentar copiar los certificados a ubicaciones compartidas en /tmp
if [ -f "/var/lib/postgresql/ssl/server.crt" ] && [ -f "/var/lib/postgresql/ssl/server.key" ]; then
  log "INFO" "Copiando certificados de PostgreSQL a /tmp/ssl para compartir..."
  mkdir -p /tmp/ssl
  cp /var/lib/postgresql/ssl/server.crt /tmp/ssl/postgres.crt
  cp /var/lib/postgresql/ssl/server.key /tmp/ssl/postgres.key
  chmod 644 /tmp/ssl/postgres.crt
  chmod 600 /tmp/ssl/postgres.key
  if getent group ssl-cert > /dev/null; then
    chown root:ssl-cert /tmp/ssl/postgres.key
    chmod 640 /tmp/ssl/postgres.key
  fi
  log "INFO" "✅ Certificados copiados y configurados en /tmp/ssl"
fi

log "INFO" "=============================================="
log "INFO" "Verificación de permisos completada"
log "INFO" "=============================================="
