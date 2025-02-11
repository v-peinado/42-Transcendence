#!/bin/bash

# Este script maneja la configuración inicial necesaria para Vault.
# Funciones:
# - Configuración del modo de operación (development/production)
# - Creación de directorios necesarios
# - Establecimiento de permisos correctos
# - Generación inicial de certificados SSL si no existen
# - Preparación del entorno para la ejecución de Vault

VAULT_MODE=${VAULT_MODE:-"production"}
VAULT_CONFIG="/etc/vault.d/config.hcl"

setup_initial() {
    mkdir -p "${LOG_DIR}"
    chmod 755 "${LOG_DIR}"
    touch "${OPERATION_LOG}"
    chmod 640 "${OPERATION_LOG}"

    if [ ! -f "/tmp/ssl/transcendence.crt" ]; then
        log_message "Generando certificados SSL..."
        /usr/local/bin/generate-ssl.sh 2>> "${ERROR_LOG}" &
    fi
}
