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
        
        if ! vault operator init -status > /dev/null 2>&1; then
            log_message "Initializing Vault..."
            vault operator init -key-shares=1 -key-threshold=1 > "${LOG_DIR}/init.txt"
            chmod 600 "${LOG_DIR}/init.txt"
            
            UNSEAL_KEY=$(grep "Unseal Key 1" "${LOG_DIR}/init.txt" | awk '{print $4}')
            ROOT_TOKEN=$(grep "Initial Root Token" "${LOG_DIR}/init.txt" | awk '{print $4}')
            
            # Save keys for unsealing in the future
            echo "$UNSEAL_KEY" > "${LOG_DIR}/unseal.key"
            echo "$ROOT_TOKEN" > "${LOG_DIR}/root.token"
            chmod 600 "${LOG_DIR}/unseal.key" "${LOG_DIR}/root.token"
            
            log_message "Unsealing Vault..."
            vault operator unseal "$UNSEAL_KEY"
            vault login "$ROOT_TOKEN"
        else
            # Recover keys from previous initialization
            UNSEAL_KEY=$(cat "${LOG_DIR}/unseal.key")
            ROOT_TOKEN=$(cat "${LOG_DIR}/root.token")
            vault operator unseal "$UNSEAL_KEY"
            vault login "$ROOT_TOKEN"
        fi
    fi
}

configure_vault() {
    # Simplificar ya que ahora manejamos el unseal directamente
    export VAULT_TOKEN
    VAULT_TOKEN=$(grep "Initial Root Token" "${LOG_DIR}/init.txt" | awk '{print $4}')
    export VAULT_ADDR='https://127.0.0.1:8200'
    
    if ! vault secrets list | grep -q '^secret/'; then
        vault secrets enable -path=secret kv-v2
        log_message "KV-2 engine enabled"
    fi

    log_message "Configuring access policies..."
    configure_policies
}

configure_policies() {
    # Configure access policies for Django
    vault policy write django - <<EOF
path "secret/data/django/*" {
    capabilities = ["read", "list"]
}
path "secret/metadata/django/*" {
    capabilities = ["list"]
}
EOF

    # Create a token for Django with the policy
    token=$(vault token create -policy=django -format=json | jq -r '.auth.client_token')
    echo "$token" > "/tmp/ssl/django_token"
    chmod 644 "/tmp/ssl/django_token"
}
