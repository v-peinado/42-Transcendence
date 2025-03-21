#!/bin/bash

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Función para imprimir mensajes formateados
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

# Verificar si estamos ejecutando como root
if [ "$(id -u)" != "0" ]; then
   log "ERROR" "Este script debe ejecutarse como root"
   exit 1
fi

# Verificar si PostgreSQL está en ejecución
if ! pg_isready -q; then
  log "ERROR" "PostgreSQL no está en ejecución"
  exit 1
fi

log "INFO" "=== Diagnóstico de conexiones SSL en PostgreSQL ==="

# 1. Verificar la configuración de PostgreSQL
log "INFO" "Verificando configuración de PostgreSQL..."
pgdata=$(psql -U postgres -t -c "SHOW data_directory;" | xargs)
ssl_status=$(psql -U postgres -t -c "SHOW ssl;" | xargs)
ssl_cert=$(psql -U postgres -t -c "SHOW ssl_cert_file;" | xargs)
ssl_key=$(psql -U postgres -t -c "SHOW ssl_key_file;" | xargs)

log "INFO" "- Directorio de datos: $pgdata"
log "INFO" "- SSL activado: $ssl_status"
log "INFO" "- Certificado SSL: $ssl_cert"
log "INFO" "- Clave SSL: $ssl_key"

# 2. Verificar archivos de certificados
log "INFO" "Verificando archivos de certificados..."

if [ -f "$ssl_cert" ]; then
  log "INFO" "- Certificado SSL encontrado: $ssl_cert"
  
  # Verificar contenido del certificado
  if openssl x509 -in "$ssl_cert" -text -noout > /dev/null 2>&1; then
    log "INFO" "- Certificado SSL válido"
    cert_subject=$(openssl x509 -in "$ssl_cert" -noout -subject)
    log "INFO" "  $cert_subject"
  else
    log "ERROR" "- Certificado SSL inválido"
  fi
else
  log "ERROR" "- Certificado SSL no encontrado: $ssl_cert"
fi

if [ -f "$ssl_key" ]; then
  log "INFO" "- Clave SSL encontrada: $ssl_key"
  
  # Verificar permisos
  if [ "$(stat -c %a "$ssl_key")" == "600" ]; then
    log "INFO" "- Permisos de clave correctos: 600"
  else
    log "WARN" "- Permisos de clave incorrectos: $(stat -c %a "$ssl_key")"
    log "INFO" "  Corrigiendo permisos..."
    chmod 600 "$ssl_key"
  fi
else
  log "ERROR" "- Clave SSL no encontrada: $ssl_key"
fi

# 3. Verificar configuración en postgresql.conf
log "INFO" "Verificando configuración en postgresql.conf..."
if [ -f "$pgdata/postgresql.conf" ]; then
  ssl_config=$(grep -E "^ssl[_=]" "$pgdata/postgresql.conf")
  echo "$ssl_config"
  
  # Verificar si SSL está activado
  if ! grep -q "^ssl = on" "$pgdata/postgresql.conf"; then
    log "WARN" "SSL no está activado explícitamente en postgresql.conf"
    log "INFO" "Activando SSL..."
    sed -i '/^ssl = off/d' "$pgdata/postgresql.conf"
    echo "ssl = on" >> "$pgdata/postgresql.conf"
    modified=true
  fi
  
  # Verificar configuración de log_connections
  if ! grep -q "^log_connections = on" "$pgdata/postgresql.conf"; then
    log "INFO" "Activando log_connections para depuración..."
    echo "log_connections = on" >> "$pgdata/postgresql.conf"
    modified=true
  fi
  
  # Verificar configuración de cifrados
  if ! grep -q "^ssl_ciphers" "$pgdata/postgresql.conf"; then
    log "INFO" "Mejorando compatibilidad con cifrados SSL..."
    echo "ssl_ciphers = 'HIGH:MEDIUM:+3DES:!aNULL'" >> "$pgdata/postgresql.conf"
    modified=true
  fi
else
  log "ERROR" "No se encontró postgresql.conf en $pgdata"
fi

# 4. Verificar pg_hba.conf
log "INFO" "Verificando configuración en pg_hba.conf..."
if [ -f "$pgdata/pg_hba.conf" ]; then
  # Contar entradas hostssl
  hostssl_count=$(grep -c "^hostssl" "$pgdata/pg_hba.conf" || echo "0")
  log "INFO" "- Entradas hostssl encontradas: $hostssl_count"
  
  # Verificar si hay entradas para permitir conexiones SSL desde cualquier dirección
  if ! grep -q "^hostssl.*all.*all.*all" "$pgdata/pg_hba.conf"; then
    log "WARN" "No se encontraron entradas hostssl para todas las direcciones"
    log "INFO" "Agregando entrada hostssl para todas las direcciones..."
    echo "hostssl all             all             all                    md5" >> "$pgdata/pg_hba.conf"
    modified=true
  fi
else
  log "ERROR" "No se encontró pg_hba.conf en $pgdata"
fi

# 5. Reiniciar PostgreSQL si se realizaron cambios
if [ "$modified" = true ]; then
  log "INFO" "Se realizaron cambios en la configuración, recargando PostgreSQL..."
  psql -U postgres -c "SELECT pg_reload_conf();"
  log "INFO" "Configuración recargada"
fi

# 6. Probar conexión SSL
log "INFO" "Probando conexión SSL..."
if PGSSLMODE=require PGPASSWORD="$POSTGRES_PASSWORD" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -h localhost -c "SELECT 'Conexión SSL exitosa';" >/dev/null 2>&1; then
  log "INFO" "✅ Conexión SSL exitosa"
else
  log "ERROR" "❌ Conexión SSL fallida"
  log "INFO" "Revisando logs de PostgreSQL para obtener más información..."
  tail -n 50 "$pgdata/log/postgresql.log" | grep -i "ssl\|connection"
fi

log "INFO" "=== Diagnóstico completado ==="
