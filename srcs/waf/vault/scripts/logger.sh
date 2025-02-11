#!/bin/bash

# Este script proporciona funciones de logging centralizadas para todos los demás scripts.
# Características:
# - Manejo de diferentes niveles de log (INFO, ERROR, WARN, DEBUG)
# - Formateo consistente de timestamps
# - Separadores visuales para mejor legibilidad
# - Logs específicos para secretos con emojis
# - Gestión de archivos de log en diferentes ubicaciones

LOG_DIR="/var/log/vault"
AUDIT_LOG="${LOG_DIR}/audit.log"
ERROR_LOG="${LOG_DIR}/error.log"
SYSTEM_LOG="${LOG_DIR}/system.log"
OPERATION_LOG="${LOG_DIR}/operation.log"

log() {
    local level=$1
    local message=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "$timestamp [$level] $message"
}

show_section() {
    echo -e "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  $1"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "${OPERATION_LOG}"
}

log_secret() {
    local path=$1
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "📦 ${timestamp} [SECRET] Secreto almacenado: $path"
    echo "   └─ Estado: ✅ Guardado correctamente"
}
