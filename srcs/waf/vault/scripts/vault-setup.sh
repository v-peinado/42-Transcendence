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

# Define modules path
MODULES_PATH="/usr/local/bin"
REQUIRED_MODULES=(
    "${MODULES_PATH}/logger.sh"
    "${MODULES_PATH}/vault-config.sh"
    "${MODULES_PATH}/vault-init.sh"
    "${MODULES_PATH}/vault-secrets.sh"
)

# Verify and load modules
for module in "${REQUIRED_MODULES[@]}"; do
    if [ ! -f "$module" ]; then
        echo "Error: Required module not found: $module"
        exit 1
    fi
    # shellcheck source=/usr/local/bin/logger.sh
    # shellcheck source=/usr/local/bin/vault-config.sh
    # shellcheck source=/usr/local/bin/vault-init.sh
    # shellcheck source=/usr/local/bin/vault-secrets.sh
    source "$module"
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
