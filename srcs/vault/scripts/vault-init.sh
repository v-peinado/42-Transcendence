#!/bin/bash

# This script manages Vault server initialization and configuration.
# Main functions:
# - Vault server initialization
# - Unseal process management
# - Access policy configuration
# - Token and key management
# - Server status monitoring
# - Security policy setup for Django and Nginx

# The script handles two operation modes:
# 1. Development: Simplified configuration for testing
# 2. Production: Secure configuration with token and unseal management

# Set environment variables upfront
export VAULT_ADDR='https://127.0.0.1:8200'
export VAULT_SKIP_VERIFY=true

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
    # Only proceed with initialization in production mode
    if [ "${VAULT_MODE}" != "production" ]; then
        return 0
    fi
    
    # Verify Vault is ready before proceeding
    if ! curl -s -k "${VAULT_ADDR}/v1/sys/health" >/dev/null 2>&1; then
        log "ERROR" "Vault is not ready for initialization"
        wait_for_vault
    fi
        
    if ! vault operator init -status > /dev/null 2>&1; then
        log_message "Initializing Vault..."
        if [ "${VAULT_LOG_TOKENS}" = "true" ]; then
            vault operator init -key-shares=1 -key-threshold=1 > "${LOG_DIR}/init.txt"
        else
            vault operator init -key-shares=1 -key-threshold=1 > "${LOG_DIR}/init.txt" 2>/dev/null
        fi
        chmod 600 "${LOG_DIR}/init.txt"
        
        UNSEAL_KEY=$(grep "Unseal Key 1" "${LOG_DIR}/init.txt" | awk '{print $4}')
        ROOT_TOKEN=$(grep "Initial Root Token" "${LOG_DIR}/init.txt" | awk '{print $4}')
        
        # Change path to persistent volume for keys
        mkdir -p /etc/vault.d/data
        echo "$UNSEAL_KEY" > "/etc/vault.d/data/unseal.key"
        echo "$ROOT_TOKEN" > "/etc/vault.d/data/root.token"
        chmod 600 "/etc/vault.d/data/unseal.key" "/etc/vault.d/data/root.token"
        
        log_message "Unsealing Vault..."
        vault operator unseal "$UNSEAL_KEY" >/dev/null 2>&1
        if [ "${VAULT_LOG_TOKENS}" = "true" ]; then
            vault login "$ROOT_TOKEN"
        else
            vault login "$ROOT_TOKEN" >/dev/null 2>&1
        fi
    else
        # Recover keys and token from persistent volume
        UNSEAL_KEY=$(cat "/etc/vault.d/data/unseal.key")
        ROOT_TOKEN=$(cat "/etc/vault.d/data/root.token")
        vault operator unseal "$UNSEAL_KEY" >/dev/null 2>&1
        if [ "${VAULT_LOG_TOKENS}" = "true" ]; then
            vault login "$ROOT_TOKEN"
        else
            vault login "$ROOT_TOKEN" >/dev/null 2>&1
        fi
    fi
    
    # Verify Vault is fully initialized and unsealed
    if ! vault status >/dev/null 2>&1; then
        log "ERROR" "❌ Failed to initialize or unseal Vault"
        return 1
    fi
    
    log "INFO" "✅ Vault is initialized and unsealed"
}

configure_vault() {
    
    if ! vault secrets list | grep -q '^secret/'; then
        vault secrets enable -path=secret kv-v2
        log_message "KV-2 engine enabled"
    fi

    log_message "Configuring access policies..."
    configure_policies
}

configure_policies() {
    # Use root's permissions to handle the shared directory
    mkdir -p /tmp/ssl
    chmod -R 777 /tmp/ssl || true

    # Configure access policies for Django with simpler and more permissive rules
    vault policy write django - <<EOF
path "secret/data/*" {
    capabilities = ["read", "list"]
}
path "secret/metadata/*" {
    capabilities = ["read", "list"]
}
EOF

    # Create token with longer TTL and proper name
    DJANGO_TOKEN=$(vault token create \
        -policy=django \
        -display-name=django \
        -ttl=720h \
        -format=json | jq -r '.auth.client_token')

    if [ -n "$DJANGO_TOKEN" ]; then
        echo "Creating token file..."
        # Use atomic file creation with proper permissions
        echo "$DJANGO_TOKEN" | tee /tmp/ssl/django_token > /dev/null
        chmod 666 /tmp/ssl/django_token || true
        
        # Verify token file creation
        if [ -f "/tmp/ssl/django_token" ] && [ -s "/tmp/ssl/django_token" ]; then
            log_message "Token file created successfully (size: $(stat -c%s /tmp/ssl/django_token) bytes)"
            log_message "Token file permissions: $(stat -c%a /tmp/ssl/django_token)"
        else
            log "ERROR" "Failed to create token file properly"
        fi
        
        log_message "Created Django token successfully"
    else
        log "ERROR" "Failed to create Django token"
        exit 1
    fi
}
