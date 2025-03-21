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
log "INFO" "Diagnóstico avanzado de error EOF en conexiones SSL"
log "INFO" "=============================================="

# 1. Verificar versión de OpenSSL
log "INFO" "Versión de OpenSSL:"
openssl version

# 2. Verificar certificados SSL
log "INFO" "Verificando certificados SSL:"
if [ -f "/var/lib/postgresql/ssl/server.crt" ]; then
    openssl x509 -in /var/lib/postgresql/ssl/server.crt -noout -text | grep "Subject:"
    openssl x509 -in /var/lib/postgresql/ssl/server.crt -noout -text | grep "Signature Algorithm:"
else
    log "ERROR" "Certificado no encontrado"
fi

# 3. Verificar configuración de PostgreSQL
log "INFO" "Configuración SSL en postgresql.conf:"
grep -E "ssl|SSL" "${PGDATA}/postgresql.conf" || echo "No SSL config found"

# 4. Verificar configuración pg_hba.conf
log "INFO" "Configuración en pg_hba.conf:"
grep "hostssl" "${PGDATA}/pg_hba.conf"

# 5. Verificar logs recientes de conexiones fallidas
log "INFO" "Logs recientes de conexiones SSL:"
grep "EOF detected" "${PGDATA}/log/postgresql-$(date +'%a').log" | tail -5 || echo "No EOF errors found"

# 6. Intentar conexiones de prueba con diferentes configuraciones SSL
log "INFO" "Probando conexiones con diferentes configuraciones SSL:"

protocols=("TLSv1.2" "TLSv1.3")
for proto in "${protocols[@]}"; do
    log "INFO" "Intentando conexión con protocolo $proto..."
    if PGSSLMODE=require SSL_VERSION=$proto psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -h localhost -c "SELECT '$proto connection successful';" > /dev/null 2>&1; then
        log "INFO" "✅ Protocolo $proto: Conexión exitosa"
    else
        log "ERROR" "❌ Protocolo $proto: Conexión fallida"
    fi
done

# 7. Recomendaciones finales
log "INFO" "=============================================="
log "INFO" "Recomendaciones para resolver error EOF:"
log "INFO" "1. Configurar Django para usar sslmode=require sin verificar certificados"
log "INFO" "2. Simplificar la lista de cifrados SSL con 'ssl_ciphers = HIGH:!aNULL:!PSK'"
log "INFO" "3. Reiniciar el contenedor de PostgreSQL Y Django después de cada cambio"
log "INFO" "4. Verificar que los certificados están correctamente copiados entre contenedores"
log "INFO" "5. Probar con una configuración mínima antes de expandir a una más compleja"
log "INFO" "=============================================="
