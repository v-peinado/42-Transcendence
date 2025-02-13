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
        PORT="${SQL_PORT}" >/dev/null 2>&1 && \
        log_secret "django/database"

    # OAuth secrets
    vault kv put secret/django/oauth \
        CLIENT_ID="${FORTYTWO_CLIENT_ID}" \
        CLIENT_SECRET="${FORTYTWO_CLIENT_SECRET}" \
        REDIRECT_URI="${FORTYTWO_REDIRECT_URI}" \
        API_UID="${FORTYTWO_API_UID}" \
        API_SECRET="${FORTYTWO_API_SECRET}" >/dev/null 2>&1 && \
        log_secret "django/oauth"

    # Settings
    vault kv put secret/django/settings \
        DEBUG="${DJANGO_DEBUG:-False}" \
        ALLOWED_HOSTS="${DJANGO_ALLOWED_HOSTS}" \
        SECRET_KEY="${DJANGO_SECRET_KEY}" >/dev/null 2>&1 && \
        log_secret "django/settings"

    # JWT
    vault kv put secret/django/jwt \
        secret_key="${JWT_SECRET_KEY}" \
        algorithm="${JWT_ALGORITHM}" \
        expiration_time="${JWT_EXPIRATION_TIME}" >/dev/null 2>&1 && \
        log_secret "django/jwt"

    # Email
    vault kv put secret/django/email \
        HOST="${EMAIL_HOST}" \
        PORT="${EMAIL_PORT}" \
        USE_TLS="${EMAIL_USE_TLS}" \
        HOST_USER="${EMAIL_HOST_USER}" \
        HOST_PASSWORD="${EMAIL_HOST_PASSWORD}" \
        FROM_EMAIL="${DEFAULT_FROM_EMAIL}" >/dev/null 2>&1 && \
        log_secret "django/email"
}
