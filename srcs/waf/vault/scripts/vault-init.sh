#!/bin/bash

# This script manages Vault server initialization and configuration.
# Main functions:
# - Vault server initialization
# - Unseal process management
# - Access policy configuration
# - Token and key management
# - Server status monitoring
# - Security policy setup for Django and Nginx
#
# The script handles two operation modes:
# 1. Development: Simplified configuration for testing
# 2. Production: Secure configuration with token and unseal management

start_vault() {
    show_section "Starting Vault"
    log "INFO" "Starting server and establishing secure TLS connection..."

    if [ "${VAULT_MODE}" = "development" ]; then
        log_message "Starting Vault in development mode..."
        vault server -dev \
            -dev-root-token-id="${VAULT_ROOT_TOKEN}" \
            -dev-listen-address="0.0.0.0:8200" \
            -log-level=error > /dev/null 2>&1 &
    else
        vault server -config="${VAULT_CONFIG}" \
            -log-level=warn > /dev/null 2>&1 &
    fi
    
    wait_for_vault
}

wait_for_vault() {
    log "INFO" "Waiting for Vault to be available..."
    local max_attempts=15
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if curl -s -k https://127.0.0.1:8200/v1/sys/health >/dev/null 2>&1; then
            log "INFO" "✅ Vault is available"
            return 0
        fi
        log "INFO" "⏳ Attempt $attempt of $max_attempts..."
        attempt=$((attempt + 1))
        sleep 2
    done

    log "ERROR" "❌ Timeout waiting for Vault"
    return 1
}

initialize_vault() {
    if [ "${VAULT_MODE}" = "production" ]; then
        export VAULT_ADDR='https://127.0.0.1:8200'
        export VAULT_SKIP_VERIFY=true
        unset VAULT_TOKEN

        log_message "Setting VAULT_ADDR=${VAULT_ADDR}"

        if ! vault operator init -status > /dev/null 2>&1; then
            log_message "Initializing Vault..."
            vault operator init -key-shares=1 -key-threshold=1 > "${LOG_DIR}/init.txt"
            chmod 600 "${LOG_DIR}/init.txt"
            chown nginxuser:nginxuser "${LOG_DIR}/init.txt"
            
            UNSEAL_KEY=$(grep "Unseal Key 1" "${LOG_DIR}/init.txt" | awk '{print $4}')
            ROOT_TOKEN=$(grep "Initial Root Token" "${LOG_DIR}/init.txt" | awk '{print $4}')
            
            log_message "Unsealing Vault..."
            vault operator unseal "$UNSEAL_KEY"
            vault login "$ROOT_TOKEN"
        fi
    fi
}

configure_vault() {
    if [ ! -f "${LOG_DIR}/init.txt" ]; then
        log "ERROR" "init.txt not found"
        return 1
    fi
    
    export VAULT_TOKEN
    VAULT_TOKEN=$(grep "Initial Root Token" "${LOG_DIR}/init.txt" | awk '{print $4}')
    export VAULT_ADDR='https://127.0.0.1:8200'
    
    until vault status >/dev/null 2>&1; do
        if vault status 2>/dev/null | grep -q "Sealed: true"; then
            UNSEAL_KEY=$(grep "Unseal Key 1" "${LOG_DIR}/init.txt" | awk '{print $4}')
            vault operator unseal "$UNSEAL_KEY"
        fi
        sleep 2
    done

    if ! vault secrets list | grep -q '^secret/'; then
        vault secrets enable -path=secret kv-v2
        log_message "KV-2 engine enabled"
    fi

    log_message "Configuring access policies..."
    configure_policies
}

configure_policies() {
    vault policy write django - <<-EOF
    # Permitir acceso a los secretos de Django
    path "secret/data/django/*" {
        capabilities = ["create", "read", "update", "delete", "list"]
    }

    # Permitir listar los secretos
    path "secret/metadata/django/*" {
        capabilities = ["list"]
    }

    # Permitir acceso a los secretos de Nginx
    path "secret/data/nginx/*" {
        capabilities = ["create", "read", "update", "delete", "list"]
    }

    path "secret/metadata/nginx/*" {
        capabilities = ["list"]
    }
    
    # Gestión de tokens
    path "auth/token/*-self" {
        capabilities = ["read", "update"]
    }
EOF
}
