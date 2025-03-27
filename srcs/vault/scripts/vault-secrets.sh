#!/bin/bash

# This script handles the secure storage of secrets in Vault.
# Responsibilities:
# - Django credentials storage
# - OAuth secrets management
# - Email configuration
# - SSL certificates storage
# - JWT token management
# - Access and permissions verification

# Implements validation and error handling for each operation
# and provides detailed feedback on each secret's status

store_secrets() {
    show_section "Storing Secrets"
    
    if ! vault token lookup >/dev/null 2>&1; then
        log "ERROR" "No Vault access"
        return 1
    fi

    # Verify critical environment variables exist
    local missing_vars=()
    
    # Check critical database variables
    for var in SQL_ENGINE POSTGRES_DB POSTGRES_USER SQL_HOST SQL_PORT; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    # Check OAuth variables
    for var in FORTYTWO_CLIENT_ID FORTYTWO_CLIENT_SECRET FORTYTWO_REDIRECT_URI; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    # Check JWT variables
    if [ -z "$JWT_SECRET_KEY" ]; then
        missing_vars+=("JWT_SECRET_KEY")
    fi
    
    # Check encryption key
    if [ -z "$ENCRYPTION_KEY" ]; then
        missing_vars+=("ENCRYPTION_KEY")
    fi
    
    # Report missing variables
    if [ ${#missing_vars[@]} -gt 0 ]; then
        log "WARNING" "Missing critical environment variables:"
        for var in "${missing_vars[@]}"; do
            log "WARNING" "- $var"
        done
        log "WARNING" "Some secrets may not be stored properly in Vault"
    fi

    # Database secrets
    vault kv put secret/django/database \
        ENGINE="${SQL_ENGINE:-}" \
        NAME="${POSTGRES_DB:-}" \
        USER="${POSTGRES_USER:-}" \
        PASSWORD="${POSTGRES_PASSWORD:-}" \
        HOST="${SQL_HOST:-}" \
        PORT="${SQL_PORT:-}" >/dev/null 2>&1 && \
        log_secret "django/database"

    # OAuth secrets
    vault kv put secret/django/oauth \
        FORTYTWO_CLIENT_ID="${FORTYTWO_CLIENT_ID:-}" \
        FORTYTWO_CLIENT_SECRET="${FORTYTWO_CLIENT_SECRET:-}" \
        FORTYTWO_REDIRECT_URI="${FORTYTWO_REDIRECT_URI:-}" \
        FORTYTWO_API_UID="${FORTYTWO_API_UID}" \
        FORTYTWO_API_SECRET="${FORTYTWO_API_SECRET}" >/dev/null 2>&1 && \
        log_secret "django/oauth"

    # Email secrets
    vault kv put secret/django/email \
        EMAIL_HOST="${EMAIL_HOST}" \
        EMAIL_PORT="${EMAIL_PORT}" \
        EMAIL_USE_TLS="${EMAIL_USE_TLS}" \
        EMAIL_HOST_USER="${EMAIL_HOST_USER}" \
        EMAIL_HOST_PASSWORD="${EMAIL_HOST_PASSWORD}" \
        DEFAULT_FROM_EMAIL="${DEFAULT_FROM_EMAIL}" >/dev/null 2>&1 && \
        log_secret "django/email"

    # Django settings
    vault kv put secret/django/settings \
        DEBUG="False" \
        ALLOWED_HOSTS="${DJANGO_ALLOWED_HOSTS}" \
        SECRET_KEY="${DJANGO_SECRET_KEY}" >/dev/null 2>&1 && \
        log_secret "django/settings"

    # JWT settings
    vault kv put secret/django/jwt \
        JWT_SECRET_KEY="${JWT_SECRET_KEY:-}" \
        JWT_ALGORITHM="${JWT_ALGORITHM}" \
        JWT_EXPIRATION_TIME="${JWT_EXPIRATION_TIME:-3600}" >/dev/null 2>&1 && \
        log_secret "django/jwt"

    # GDPR encryption key
    vault kv put secret/django/gdpr \
        ENCRYPTION_KEY="${ENCRYPTION_KEY:-}" >/dev/null 2>&1 && \
        log_secret "django/gdpr"

    # Celery settings
    vault kv put secret/django/celery \
        CELERY_USER="${CELERY_USER}" \
        CELERY_PGSSLMODE="${CELERY_PGSSLMODE}" \
        CELERY_PGAPPNAME="${CELERY_PGAPPNAME}" \
        CELERY_PGSSLCERT="${CELERY_PGSSLCERT}" \
        CELERY_PGSSLKEY="${CELERY_PGSSLKEY}" >/dev/null 2>&1 && \
        log_secret "django/celery"

    # Verify all secrets were stored
    for path in "database" "oauth" "email" "settings" "jwt" "gdpr" "celery"; do
        if ! vault kv get secret/django/${path} >/dev/null 2>&1; then
            log "ERROR" "Failed to verify secret: django/${path}"
            return 1
        fi
    done
    
    store_ssl_certificates
    
    log_message "All secrets stored and verified successfully"
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
