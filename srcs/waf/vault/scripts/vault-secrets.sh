#!/bin/bash

# This script handles the secure storage of secrets in Vault.
# Responsibilities:
# - Django credentials storage
# - OAuth secrets management
# - Email configuration
# - SSL certificates storage
# - JWT token management
# - Access and permissions verification
#
# Implements validation and error handling for each operation
# and provides detailed feedback on each secret's status

store_secrets() {
    show_section "Storing Secrets"
    
    if ! vault token lookup >/dev/null 2>&1; then
        log "ERROR" "No Vault access"
        return 1
    fi

    store_secret "django/database" "ENGINE NAME USER PASSWORD HOST PORT"
    store_secret "django/oauth" "CLIENT_ID CLIENT_SECRET REDIRECT_URI API_UID API_SECRET"
    store_secret "django/email" "HOST PORT USE_TLS HOST_USER HOST_PASSWORD FROM_EMAIL"
    store_secret "django/settings" "DEBUG ALLOWED_HOSTS SECRET_KEY"
    store_secret "django/jwt" "secret_key algorithm expiration_time"
    store_ssl_certificates

    # JWT settings
    vault kv put secret/django/jwt \
        JWT_SECRET_KEY="${JWT_SECRET_KEY}" \
        JWT_ALGORITHM="${JWT_ALGORITHM}" \
        JWT_EXPIRATION_TIME="${JWT_EXPIRATION_TIME:-3600}" >/dev/null 2>&1 && \
        log_secret "django/jwt"
}

store_secret() {
    local path=$1
    local vars=$2
    local -a value_args=()
    
    for var in $vars; do
        value_args+=("${var}=${!var}")
    done

    if vault kv put "secret/$path" "${value_args[@]}" >/dev/null 2>&1; then
        log_secret "$path"
    else
        log "ERROR" "Failed to store secret: $path"
        return 1
    fi
}

store_ssl_certificates() {
    if vault kv put secret/nginx/ssl \
        ssl_certificate="$(base64 /tmp/ssl/transcendence.crt 2>/dev/null || echo '')" \
        ssl_certificate_key="$(base64 /tmp/ssl/transcendence.key 2>/dev/null || echo '')" >/dev/null 2>&1; then
        log_secret "nginx/ssl"
    else
        log "ERROR" "Failed to store SSL certificates"
        return 1
    fi
}
