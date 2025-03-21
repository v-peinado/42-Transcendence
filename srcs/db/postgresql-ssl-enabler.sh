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
  
  log "INFO" "Verificando la configuración SSL actual..."
  current_ssl=$(psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SHOW ssl;")
  log "INFO" "Configuración SSL actual: $current_ssl"
  
  if [[ "$current_ssl" == *"on"* ]]; then
    log "INFO" "SSL ya está activado en PostgreSQL"
  else
    log "WARN" "SSL está desactivado, intentando activarlo..."
    
    # Primero, verificar la presencia de los certificados
    if [ ! -f "/var/lib/postgresql/ssl/server.crt" ] || [ ! -f "/var/lib/postgresql/ssl/server.key" ]; then
      log "ERROR" "Certificados SSL no encontrados en la ubicación esperada"
      return 1
    fi
    
    # Intentar activar SSL a través de ALTER SYSTEM
    if psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "ALTER SYSTEM SET ssl = 'on';" 2>/dev/null; then
      log "INFO" "Configuración SSL cambiada exitosamente"
      
      # Establecer otras configuraciones SSL necesarias
      psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "ALTER SYSTEM SET ssl_cert_file = '/var/lib/postgresql/ssl/server.crt';"
      psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "ALTER SYSTEM SET ssl_key_file = '/var/lib/postgresql/ssl/server.key';"
      psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "ALTER SYSTEM SET ssl_ca_file = '/var/lib/postgresql/ssl/server.crt';"
      
      # Recargar la configuración
      log "INFO" "Recargando configuración de PostgreSQL..."
      if psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT pg_reload_conf();" | grep -q 't'; then
        log "INFO" "Configuración de PostgreSQL recargada exitosamente"
      else
        log "ERROR" "Error al recargar la configuración de PostgreSQL"
        return 1
      fi
    else
      log "ERROR" "No se pudo cambiar la configuración SSL a través de SQL"
      log "WARN" "Intentando modificar directamente postgresql.conf..."
      
      # Obtener la ubicación de postgresql.conf
      conf_file=$(psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SHOW config_file;")
      conf_file=$(echo $conf_file | tr -d ' ')
      
      if [ -w "$conf_file" ]; then
        log "INFO" "Modificando $conf_file directamente..."
        # Hacer una copia de seguridad
        cp "$conf_file" "${conf_file}.bak"
        
        # Reemplazar o agregar ssl = on
        if grep -q "ssl = " "$conf_file"; then
          sed -i 's/ssl = off/ssl = on/' "$conf_file"
        else
          echo "ssl = on" >> "$conf_file"
        fi
        
        # Reiniciar PostgreSQL
        log "WARN" "Es necesario reiniciar PostgreSQL para aplicar los cambios"
        return 0
      else
        log "ERROR" "No se puede escribir en el archivo de configuración: $conf_file"
        return 1
      fi
    fi
    
    # Verificar nuevamente la configuración SSL
    new_ssl=$(psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SHOW ssl;")
    if [[ "$new_ssl" == *"on"* ]]; then
      log "INFO" "✅ SSL activado exitosamente"
    else
      log "ERROR" "❌ SSL sigue desactivado después de los intentos de activación"
      return 1
    fi
  fi
  
  # Intentar una conexión SSL
  log "INFO" "Probando conexión SSL..."
  if PGSSLMODE=require psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -h localhost -c "SELECT 'SSL connection successful';" 2>/dev/null; then
    log "INFO" "✅ Conexión SSL exitosa"
  else
    log "ERROR" "❌ Falló la conexión SSL"
    log "WARN" "Es posible que se requiera un reinicio completo de PostgreSQL"
    return 1
  fi
  
  log "INFO" "Proceso de activación de SSL completado"
  return 0
}

# Función principal
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
    log "INFO" "SSL activado correctamente en PostgreSQL"
    exit 0
  else
    log "ERROR" "No se pudo activar SSL en PostgreSQL"
    exit 1
  fi
}

# Ejecutar la función principal
main "$@"
