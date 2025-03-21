#!/bin/bash

set -e

# Define colores para la salida
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # Sin Color

# Función para imprimir mensajes
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

# Función principal para activar SSL en PostgreSQL
enable_ssl() {
  log "INFO" "Iniciando activación de SSL para PostgreSQL..."
  
  # Verificar si PostgreSQL está en ejecución
  if ! pg_isready -q; then
    log "ERROR" "PostgreSQL no está en ejecución"
    return 1
  fi
  
  log "INFO" "Verificando certificados SSL..."
  if [ ! -f "/var/lib/postgresql/ssl/server.crt" ] || [ ! -f "/var/lib/postgresql/ssl/server.key" ]; then
    log "ERROR" "Certificados SSL no encontrados. Copiando desde /tmp/ssl si están disponibles..."
    mkdir -p /var/lib/postgresql/ssl
    
    if [ -f "/tmp/ssl/transcendence.crt" ] && [ -f "/tmp/ssl/transcendence.key" ]; then
      cp /tmp/ssl/transcendence.crt /var/lib/postgresql/ssl/server.crt
      cp /tmp/ssl/transcendence.key /var/lib/postgresql/ssl/server.key
      chmod 600 /var/lib/postgresql/ssl/server.key
      chmod 644 /var/lib/postgresql/ssl/server.crt
      chown -R postgres:postgres /var/lib/postgresql/ssl
      log "INFO" "Certificados copiados exitosamente"
    else
      log "ERROR" "Certificados no encontrados en /tmp/ssl"
      return 1
    fi
  fi
  
  log "INFO" "Verificando la configuración SSL actual en postgresql.conf..."
  if [ -f "${PGDATA}/postgresql.conf" ]; then
    # Eliminar líneas comentadas que podrían causar confusión
    sed -i '/^#ssl = /d' "${PGDATA}/postgresql.conf"
    
    # Asegurarse de que ssl = on está presente y no comentado
    if grep -q "^ssl = off" "${PGDATA}/postgresql.conf"; then
      sed -i 's/^ssl = off/ssl = on/' "${PGDATA}/postgresql.conf"
      log "INFO" "Cambiada configuración 'ssl = off' a 'ssl = on'"
    elif ! grep -q "^ssl = on" "${PGDATA}/postgresql.conf"; then
      echo "ssl = on" >> "${PGDATA}/postgresql.conf"
      log "INFO" "Agregada configuración 'ssl = on'"
    fi
    
    # Configurar las rutas de los certificados SSL
    for param in "ssl_cert_file" "ssl_key_file" "ssl_ca_file"; do
      file_path="/var/lib/postgresql/ssl/server.crt"
      if [ "$param" = "ssl_key_file" ]; then
        file_path="/var/lib/postgresql/ssl/server.key"
      fi
      
      # Eliminar entradas comentadas
      sed -i "/^#$param = /d" "${PGDATA}/postgresql.conf"
      
      # Verificar si existe la configuración
      if ! grep -q "^$param = " "${PGDATA}/postgresql.conf"; then
        echo "$param = '$file_path'" >> "${PGDATA}/postgresql.conf"
        log "INFO" "Agregada configuración $param = '$file_path'"
      fi
    done
    
    log "INFO" "Configuración SSL en postgresql.conf modificada. Se requiere recargar la configuración."
  else
    log "ERROR" "No se encontró postgresql.conf"
    return 1
  fi
  
  log "INFO" "Intentando activar SSL a través de SQL..."
  if psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "ALTER SYSTEM SET ssl = 'on';" 2>/dev/null; then
    log "INFO" "Configuración SSL cambiada exitosamente en PostgreSQL"
  else
    log "WARN" "No se pudo cambiar la configuración SSL a través de SQL"
  fi
  
  log "INFO" "Intentando recargar la configuración de PostgreSQL..."
  if psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT pg_reload_conf();" | grep -q 't'; then
    log "INFO" "Configuración de PostgreSQL recargada exitosamente"
  else
    log "WARN" "No se pudo recargar la configuración de PostgreSQL"
    log "WARN" "Es posible que se requiera reiniciar PostgreSQL para aplicar los cambios"
  fi
  
  log "INFO" "Verificando estado actual de SSL..."
  current_ssl=$(psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SHOW ssl;")
  log "INFO" "Estado actual de SSL: $current_ssl"
  
  if [[ "$current_ssl" == *"on"* ]]; then
    log "INFO" "✅ SSL está activado correctamente"
  else
    log "WARN" "❌ SSL sigue desactivado después de los intentos de activación"
    log "WARN" "Se recomienda reiniciar PostgreSQL"
  fi
  
  log "INFO" "Proceso completado"
  return 0
}

main() {
  # Si no hay variables de entorno cargadas, intentar cargarlas
  if [ -z "$POSTGRES_USER" ] || [ -z "$POSTGRES_DB" ]; then
    if [ -f "/tmp/ssl/db.env" ]; then
      source /tmp/ssl/db.env
    else
      export POSTGRES_USER="vpeinado"
      export POSTGRES_DB="transcendence"
      log "WARN" "Variables de entorno no encontradas, usando valores predeterminados"
    fi
  fi
  
  # Ejecutar la activación de SSL
  if enable_ssl; then
    log "INFO" "Proceso de activación de SSL completado correctamente"
    exit 0
  else
    log "ERROR" "Error en el proceso de activación de SSL"
    exit 1
  fi
}

# Ejecutar función principal
main "$@"
