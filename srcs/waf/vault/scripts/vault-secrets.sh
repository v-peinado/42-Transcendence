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

    # Database secrets
    vault kv put secret/django/database \
        ENGINE="${SQL_ENGINE}" \
        NAME="${POSTGRES_DB}" \
        USER="${POSTGRES_USER}" \
        PASSWORD="${POSTGRES_PASSWORD}" \
        HOST="${SQL_HOST}" \
        PORT="${SQL_PORT}"

    # OAuth secrets
    vault kv put secret/django/oauth \
        CLIENT_ID="${FORTYTWO_CLIENT_ID}" \
        CLIENT_SECRET="${FORTYTWO_CLIENT_SECRET}" \
        REDIRECT_URI="${FORTYTWO_REDIRECT_URI}" \
        API_UID="${FORTYTWO_API_UID}" \
        API_SECRET="${FORTYTWO_API_SECRET}"

    # Settings
    vault kv put secret/django/settings \
        DEBUG="${DJANGO_DEBUG:-False}" \
        ALLOWED_HOSTS="${DJANGO_ALLOWED_HOSTS}" \
        SECRET_KEY="${DJANGO_SECRET_KEY}"

    # JWT
    vault kv put secret/django/jwt \
        secret_key="${JWT_SECRET_KEY}" \
        algorithm="${JWT_ALGORITHM}" \
        expiration_time="${JWT_EXPIRATION_TIME}"

    # Email
    vault kv put secret/django/email \
        HOST="${EMAIL_HOST}" \
        PORT="${EMAIL_PORT}" \
        USE_TLS="${EMAIL_USE_TLS}" \
        HOST_USER="${EMAIL_HOST_USER}" \
        HOST_PASSWORD="${EMAIL_HOST_PASSWORD}" \
        FROM_EMAIL="${DEFAULT_FROM_EMAIL}"
}

store_secret() {
    local path=$1
    local vars=$2
    local -a value_args=()
    
    for var in $vars; do
        if [ -n "${!var}" ]; then
            value_args+=("${var}=${!var}")
        else
            log "WARNING" "Empty value for $var"
        fi
    done

    if [ ${#value_args[@]} -eq 0 ]; then
        log "ERROR" "No valid values to store for $path"
        return 1
    fi

    if vault kv put "secret/$path" "${value_args[@]}" >/dev/null 2>&1; then
        log_secret "$path"
        vault kv get "secret/$path" >/dev/null 2>&1 || log "ERROR" "Failed to verify secret: $path"
    else
        log "ERROR" "Failed to store secret: $path"
        return 1
    fi
}

# store_ssl_certificates() {
#     if vault kv put secret/nginx/ssl \
#         ssl_certificate="$(base64 /tmp/ssl/transcendence.crt 2>/dev/null || echo '')" \
#         ssl_certificate_key="$(base64 /tmp/ssl/transcendence.key 2>/dev/null || echo '')" >/dev/null 2>&1; then
#         log_secret "nginx/ssl"
#     else
#         log "ERROR" "Failed to store SSL certificates"
#         return 1
#     fi
# }
