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
log "INFO" "Verificación de conexiones SSL de Django"
log "INFO" "=============================================="

# Verificar si PostgreSQL está en ejecución
if ! pg_isready -q; then
  log "ERROR" "PostgreSQL no está en ejecución"
  exit 1
fi

# Verificando la estructura de pg_stat_ssl para ajustar la consulta
PG_VERSION=$(psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SHOW server_version;" | xargs)
log "INFO" "Versión de PostgreSQL detectada: $PG_VERSION"

# Obtener la lista de columnas disponibles en pg_stat_ssl
log "INFO" "Identificando columnas disponibles en pg_stat_ssl..."
COLUMNS=$(psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "
  SELECT column_name FROM information_schema.columns 
  WHERE table_name = 'pg_stat_ssl';" | tr '\n' ' ')

log "INFO" "Columnas encontradas: $COLUMNS"

# Verificar consulta base sin columnas problemáticas
log "INFO" "Conexiones SSL activas:"
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
SELECT 
    sa.datname AS database,
    sa.usename AS user,
    sa.application_name,
    sa.client_addr,
    sa.client_port,
    ssl.ssl AS ssl_active
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
# Usando host() para convertir a texto y luego comprobar si empieza por 172.
log "INFO" "Conexiones desde Django (identificado por IP de contenedor):"
django_connections=$(psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "
SELECT COUNT(*) 
FROM pg_stat_ssl ssl
JOIN pg_stat_activity sa ON ssl.pid = sa.pid
WHERE host(sa.client_addr) ~ '^172\.' AND ssl.ssl = 't';
")

django_connections=$(echo "$django_connections" | tr -d '[:space:]')

if [ "$django_connections" = "0" ]; then
  log "WARN" "No se encontraron conexiones SSL desde Django"
  
  # Verificar conexiones no-SSL desde Django
  non_ssl_django=$(psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "
  SELECT COUNT(*) 
  FROM pg_stat_ssl ssl
  JOIN pg_stat_activity sa ON ssl.pid = sa.pid
  WHERE host(sa.client_addr) ~ '^172\.' AND ssl.ssl = 'f';
  ")
  
  non_ssl_django=$(echo "$non_ssl_django" | tr -d '[:space:]')
  
  if [ "$non_ssl_django" != "0" ]; then
    log "ERROR" "Se encontraron $non_ssl_django conexiones NO-SSL desde Django"
    log "ERROR" "Django no está usando TLS para conectarse a PostgreSQL!"
    
    # Mostrar detalles de estas conexiones no-SSL
    log "INFO" "Detalles de conexiones no-SSL desde Django:"
    psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
    SELECT 
        sa.datname AS database,
        sa.usename AS user,
        sa.application_name,
        sa.client_addr,
        sa.client_port,
        sa.backend_start,
        sa.query
    FROM 
        pg_stat_ssl ssl
    JOIN 
        pg_stat_activity sa ON ssl.pid = sa.pid
    WHERE 
        host(sa.client_addr) ~ '^172\.' AND ssl.ssl = 'f'
    LIMIT 5;
    "
  else
    log "INFO" "No se encontraron conexiones de Django (ni SSL ni no-SSL)"
  fi
else
  log "INFO" "✅ Django está usando correctamente TLS para conectarse ($django_connections conexiones)"
  
  # Mostrar detalles de estas conexiones SSL
  log "INFO" "Detalles de conexiones SSL desde Django:"
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
  SELECT 
      sa.datname AS database,
      sa.usename AS user,
      sa.application_name,
      sa.client_addr,
      sa.client_port
  FROM 
      pg_stat_ssl ssl
  JOIN 
      pg_stat_activity sa ON ssl.pid = sa.pid
  WHERE 
      host(sa.client_addr) ~ '^172\.' AND ssl.ssl = 't'
  LIMIT 5;
  "
fi

log "INFO" "=============================================="
log "INFO" "Configuración SSL de PostgreSQL:"
log "INFO" "=============================================="

psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SHOW ssl;"
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SHOW ssl_cert_file;"
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SHOW ssl_key_file;"
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SHOW ssl_ca_file;"
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SHOW ssl_ciphers;"

log "INFO" "=============================================="
log "INFO" "Prueba de conexión SSL:"
log "INFO" "=============================================="

# Intentar una conexión SSL explícita para verificar
if PGSSLMODE=require psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -h localhost -c "SELECT 'Conexión SSL exitosa';" 2>/dev/null; then
  log "INFO" "✅ Prueba de conexión SSL exitosa"
else
  log "ERROR" "❌ Prueba de conexión SSL fallida"
  # Mostrar conexiones activas para ayudar a diagnosticar
  log "INFO" "Conexiones actuales en PostgreSQL:"
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT datname, usename, application_name, client_addr FROM pg_stat_activity WHERE backend_type = 'client backend';"
fi

log "INFO" "=============================================="
log "INFO" "Verificación completada"
log "INFO" "=============================================="
