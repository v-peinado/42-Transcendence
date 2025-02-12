#!/bin/bash

# This is the main script that orchestrates the entire configuration process.
# Responsibilities:
# - Loading required modules
# - Coordinating initialization sequence
# - Dependency validation
# - Global error handling
# - Cleanup of sensitive variables
# - Starting nginx server
#
# The script ensures each step completes successfully
# before proceeding to the next one, providing
# a robust and secure system initialization.

# Load required modules
for module in logger.sh vault-config.sh vault-init.sh vault-secrets.sh; do
    if [ -f "/usr/local/bin/${module}" ]; then
        source "/usr/local/bin/${module}"
    else
        echo "Error: No se encuentra el módulo ${module}"
        exit 1
    fi
done

# Inicializar servicios en orden
setup_initial || exit 1
start_vault || exit 1
initialize_vault || exit 1
configure_vault || exit 1
store_secrets || exit 1

# Limpiar variables sensibles
unset VAULT_TOKEN
trap 'unset VAULT_TOKEN' EXIT

# Iniciar nginx
exec nginx -g 'daemon off;'
