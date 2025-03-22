#!/bin/bash

# This script handles the initial configuration required for Vault.
# Functions:
# - Operation mode setup (development/production)
# - Required directory creation
# - Proper permissions setup
# - Initial SSL certificate generation if not present
# - Environment preparation for Vault execution

VAULT_MODE=${VAULT_MODE:-"production"}
export VAULT_CONFIG="/etc/vault.d/config.hcl"

setup_initial() {
    mkdir -p "${LOG_DIR}"
    chmod 755 "${LOG_DIR}"
    touch "${OPERATION_LOG}"
    chmod 640 "${OPERATION_LOG}"

    if [ ! -f "/tmp/ssl/transcendence.crt" ]; then
        log_message "Generating SSL certificates..."
        /usr/local/bin/generate-ssl.sh 2>> "${ERROR_LOG}" &
    fi
}
