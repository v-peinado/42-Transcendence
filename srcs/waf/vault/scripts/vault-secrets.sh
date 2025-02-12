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
    show_section "Almacenando Secretos"
    
    if ! vault token lookup >/dev/null 2>&1; then
        log "ERROR" "Sin acceso a Vault"
        return 1
    fi

    store_secret "django/database" "ENGINE NAME USER PASSWORD HOST PORT"
    store_secret "django/oauth" "CLIENT_ID CLIENT_SECRET REDIRECT_URI API_UID API_SECRET"
    store_secret "django/email" "HOST PORT USE_TLS HOST_USER HOST_PASSWORD FROM_EMAIL"
    store_secret "django/settings" "DEBUG ALLOWED_HOSTS SECRET_KEY"
    store_secret "django/jwt" "secret_key algorithm expiration_time"
    store_ssl_certificates
}

store_secret() {
    local path=$1
    local vars=$2
    local values=""
    
    for var in $vars; do
        values+="${var}=\"${!var}\" "
    done

    if vault kv put "secret/$path" ${values} >/dev/null 2>&1; then
        log_secret "$path"
    else
        log "ERROR" "Fallo al almacenar secreto: $path"
        return 1
    fi
}

store_ssl_certificates() {
    if vault kv put secret/nginx/ssl \
        ssl_certificate="$(base64 /tmp/ssl/transcendence.crt 2>/dev/null || echo '')" \
        ssl_certificate_key="$(base64 /tmp/ssl/transcendence.key 2>/dev/null || echo '')" >/dev/null 2>&1; then
        log_secret "nginx/ssl"
    else
        log "ERROR" "Fallo al almacenar certificados SSL"
        return 1
    fi
}
