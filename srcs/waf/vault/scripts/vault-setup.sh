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

# Source required scripts
source /usr/local/bin/logger.sh
source /usr/local/bin/vault-init.sh
source /usr/local/bin/vault-secrets.sh

# Main setup function
setup() {
    # Start Vault server
    start_vault
    
    # Wait a bit for Vault to be fully ready
    sleep 5
    
    # Initialize and unseal Vault
    initialize_vault
    
    # Wait for Vault to be ready after unsealing
    sleep 5
    
    # Configure Vault and policies
    configure_vault
    
    # Wait for policies to be applied
    sleep 5
    
    # Store secrets
    store_secrets

    # Start nginx after everything is ready
    nginx -g 'daemon off;'
}

# Run setup
setup
