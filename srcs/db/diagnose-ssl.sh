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

# Diagnóstico avanzado de configuración SSL de PostgreSQL
diagnose_postgres_ssl() {
  log "INFO" "=============================================="
  log "INFO" "PostgreSQL SSL Diagnostic Tool"
  log "INFO" "=============================================="
  
  # Verificar si PostgreSQL está en ejecución
  if ! pg_isready -q; then
    log "ERROR" "PostgreSQL no está en ejecución"
    return 1
  fi
  log "INFO" "PostgreSQL está en ejecución"
  
  # Verificar directorios SSL
  log "INFO" "Verificando directorios SSL:"
  ls -la /var/lib/postgresql/ssl/ || log "ERROR" "Directorio SSL no encontrado"
  
  # Verificar archivos de certificados
  log "INFO" "Verificando archivos de certificados:"
  if [ -f "/var/lib/postgresql/ssl/server.crt" ]; then
    log "INFO" "Archivo de certificado existe"
    openssl x509 -in /var/lib/postgresql/ssl/server.crt -noout -text | grep "Subject:" || log "ERROR" "Certificado inválido"
  else
    log "ERROR" "Archivo de certificado no encontrado"
  fi
  
  if [ -f "/var/lib/postgresql/ssl/server.key" ]; then
    log "INFO" "Archivo de clave existe"
  else
    log "ERROR" "Archivo de clave no encontrado"
  fi
  
  # Verificar configuración de PostgreSQL
  log "INFO" "Configuración SSL de PostgreSQL:"
  
  # Mostrar configuración actual en postgresql.conf
  log "INFO" "Contenido de postgresql.conf relacionado con SSL:"
  grep -E "ssl|SSL" "${PGDATA}/postgresql.conf" || log "ERROR" "No se encontró configuración SSL en postgresql.conf"
  
  # Verificar configuración a través de SQL
  log "INFO" "Configuración SSL a través de SQL:"
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SHOW ssl;"
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SHOW ssl_cert_file;"
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SHOW ssl_key_file;"
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SHOW ssl_ca_file;"
  
  # Probar conexión estándar
  log "INFO" "Probando conexión estándar:"
  PGPASSWORD="$POSTGRES_PASSWORD" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -h localhost -c "SELECT version();" && \
    log "INFO" "Conexión estándar funciona" || log "ERROR" "Conexión estándar falló"
  
  # Probar conexión SSL explícita
  log "INFO" "Probando conexión SSL explícita:"
  PGSSLMODE=require PGPASSWORD="$POSTGRES_PASSWORD" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -h localhost \
    -c "SELECT ssl, version FROM pg_stat_ssl JOIN pg_stat_activity ON pg_stat_ssl.pid = pg_stat_activity.pid WHERE pg_stat_activity.backend_type = 'client backend' LIMIT 1;" && \
    log "INFO" "Conexión SSL funciona" || log "ERROR" "Conexión SSL falló"
  
  # Verificar conexiones SSL en pg_stat_ssl
  log "INFO" "Conexiones SSL actuales:"
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT count(*) FROM pg_stat_ssl WHERE ssl = 't';"
  
  # Intentar solucionar problemas de SSL
  log "INFO" "Intentando corregir configuración SSL..."
  
  # 1. Verificar si SSL está activado
  ssl_status=$(psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SHOW ssl;" | tr -d '[:space:]')
  if [ "$ssl_status" != "on" ]; then
    log "WARN" "SSL está desactivado, intentando activarlo..."
    psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "ALTER SYSTEM SET ssl = 'on';"
    psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT pg_reload_conf();"
    
    # Verificar nuevamente
    new_ssl=$(psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SHOW ssl;" | tr -d '[:space:]')
    if [ "$new_ssl" = "on" ]; then
      log "INFO" "SSL activado exitosamente mediante SQL"
    else
      log "WARN" "No se pudo activar SSL mediante SQL, intentando modificar postgresql.conf directamente..."
      
      # Modificar postgresql.conf directamente
      if [ -f "${PGDATA}/postgresql.conf" ]; then
        # Eliminar líneas comentadas que podrían causar confusión
        sed -i '/^#ssl = /d' "${PGDATA}/postgresql.conf"
        
        # Asegurarse de que ssl = on está presente y no comentado
        if grep -q "^ssl = off" "${PGDATA}/postgresql.conf"; then
          sed -i 's/^ssl = off/ssl = on/' "${PGDATA}/postgresql.conf"
        elif ! grep -q "^ssl = on" "${PGDATA}/postgresql.conf"; then
          echo "ssl = on" >> "${PGDATA}/postgresql.conf"
        fi
        
        log "WARN" "Se modificó postgresql.conf, se requiere reiniciar PostgreSQL"
      else
        log "ERROR" "No se pudo encontrar postgresql.conf"
      fi
    fi
  fi
  
  log "INFO" "=============================================="
  log "INFO" "Diagnóstico completado"
}

# Función principal
main() {
  # Cargar variables de entorno si están disponibles
  if [ -f "/tmp/ssl/db.env" ]; then
    source /tmp/ssl/db.env
  fi
  
  # Ejecutar diagnóstico
  diagnose_postgres_ssl
}

main "$@"
