#!/bin/bash

# Script para verificar conexiones SSL activas de Django a PostgreSQL

set -e

# Colores para salida
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

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

log "INFO" "=============================================="
log "INFO" "Verificación de conexiones SSL de Django"
log "INFO" "=============================================="

# Verificar si PostgreSQL está en ejecución
if ! pg_isready -q; then
  log "ERROR" "PostgreSQL no está en ejecución"
  exit 1
fi

# Mostrar todas las conexiones activas con información SSL
log "INFO" "Conexiones SSL activas:"
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
SELECT 
    sa.datname AS database,
    sa.usename AS user,
    sa.application_name,
    sa.client_addr,
    sa.client_port,
    ssl.ssl AS ssl_active,
    ssl.ssl_version,
    ssl.ssl_cipher,
    ssl.ssl_bits
FROM 
    pg_stat_ssl ssl
JOIN 
    pg_stat_activity sa ON ssl.pid = sa.pid
WHERE 
    sa.backend_type = 'client backend'
ORDER BY 
    ssl.ssl DESC, sa.client_addr;
"

# Contar conexiones SSL vs no-SSL
log "INFO" "Resumen de conexiones:"
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
"

# Verificar conexiones específicamente desde el contenedor Django
log "INFO" "Conexiones desde Django (identificado por IP de contenedor):"
django_connections=$(psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "
SELECT COUNT(*) 
FROM pg_stat_ssl ssl
JOIN pg_stat_activity sa ON ssl.pid = sa.pid
WHERE sa.client_addr LIKE '172.%' AND ssl.ssl = 't';
")

django_connections=$(echo "$django_connections" | tr -d '[:space:]')

if [ "$django_connections" = "0" ]; then
  log "WARN" "No se encontraron conexiones SSL desde Django"
  
  # Verificar conexiones no-SSL desde Django
  non_ssl_django=$(psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "
  SELECT COUNT(*) 
  FROM pg_stat_ssl ssl
  JOIN pg_stat_activity sa ON ssl.pid = sa.pid
  WHERE sa.client_addr LIKE '172.%' AND ssl.ssl = 'f';
  ")
  
  non_ssl_django=$(echo "$non_ssl_django" | tr -d '[:space:]')
  
  if [ "$non_ssl_django" != "0" ]; then
    log "ERROR" "Se encontraron $non_ssl_django conexiones NO-SSL desde Django"
    log "ERROR" "Django no está usando TLS para conectarse a PostgreSQL!"
  else
    log "INFO" "No se encontraron conexiones de Django (ni SSL ni no-SSL)"
  fi
else
  log "INFO" "✅ Django está usando correctamente TLS para conectarse ($django_connections conexiones)"
fi

log "INFO" "=============================================="
log "INFO" "Verificación completada"
log "INFO" "=============================================="
