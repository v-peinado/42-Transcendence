#!/bin/bash

set -e  # Exit on error

# Global variables
TOKEN_FILE="/tmp/ssl/django_token"
VAULT_ADDR="https://waf:8200"
SECRET_PATH="v1/secret/data/django/database"

MAX_ATTEMPTS=45
ATTEMPT=1
RETRY_DELAY=5

# Function to retrieve the token from the token file
get_token() {
    if [ -f "/tmp/ssl/django_token" ]; then
        cat "/tmp/ssl/django_token"
    else
        echo ""
    fi
}

# Wait for Vault to be ready with retries
wait_for_vault() {
    echo "Waiting for Vault to be ready..."
    local max_attempts=30
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if curl -sf -k "https://waf:8200/v1/sys/health" > /dev/null 2>&1; then
            echo "✅ Vault is ready!"
            return 0
        fi
        echo "⏳ Attempt $attempt of $max_attempts - Vault is unavailable, sleeping..."
        attempt=$((attempt + 1))
        sleep 2
    done

    echo "❌ Error: Timeout waiting for Vault"
    return 1
}

# Wait for token to be created
wait_for_token() {
    echo "Waiting for Vault token to be created..."
    local max_attempts=60
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if [ -f "/tmp/ssl/django_token" ] && [ -s "/tmp/ssl/django_token" ]; then
            echo "✅ Token file found and not empty"
            return 0
        fi
        echo "⏳ Attempt $attempt of $max_attempts - Waiting for token..."
        attempt=$((attempt + 1))
        sleep 2
    done

    echo "❌ Error: Timeout waiting for token"
    return 1
}

# Get secrets from Vault
get_db_secrets() {
    local token
    token=$(cat "$TOKEN_FILE")
    
    echo "🔑 Token found, attempting to fetch secrets..."

    local response
    response=$(curl -sf -k \
        --header "X-Vault-Token: $token" \
        --header "Content-Type: application/json" \
        "${VAULT_ADDR}/${SECRET_PATH}")

    if [ $? -ne 0 ]; then
        echo "❌ Error: Failed to fetch secrets from Vault"
        return 1
    fi

    # Verify if the response contains the expected data
    if ! echo "$response" | jq -e '.data.data' > /dev/null 2>&1; then
        echo "❌ Error: Invalid response format from Vault"
        return 1
    fi

    # Extract and verify values from the response
    POSTGRES_DB=$(echo "$response" | jq -r '.data.data.NAME')
    POSTGRES_USER=$(echo "$response" | jq -r '.data.data.USER')
    POSTGRES_PASSWORD=$(echo "$response" | jq -r '.data.data.PASSWORD')

    # Verify all required values are present
    if [ -z "$POSTGRES_DB" ] || [ -z "$POSTGRES_USER" ] || [ -z "$POSTGRES_PASSWORD" ]; then
        echo "❌ Error: Missing required database credentials from Vault"
        return 1
    fi

    # Export variables for use in the application
    export POSTGRES_DB
    export POSTGRES_USER
    export POSTGRES_PASSWORD

    echo "✅ Database credentials successfully loaded from Vault"
    return 0
}

# Wait for secrets to be stored in Vault
wait_for_secrets() {
    echo "Waiting for Vault secrets to be stored..."
    local max_attempts=60
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if [ -f "$TOKEN_FILE" ]; then
            local token
            token=$(cat "$TOKEN_FILE")
            
            local response
            response=$(curl -sf -k \
                --header "X-Vault-Token: $token" \
                --header "Content-Type: application/json" \
                "${VAULT_ADDR}/${SECRET_PATH}")

            if [ $? -eq 0 ] && echo "$response" | jq -e '.data.data' > /dev/null 2>&1; then
                echo "✅ Secrets found in Vault"
                return 0
            fi
        fi
        echo "⏳ Attempt $attempt of $max_attempts - Waiting for secrets..."
        attempt=$((attempt + 1))
        sleep 2
    done

    echo "❌ Error: Timeout waiting for secrets"
    return 1
}

# Main function to retrieve secrets from Vault
get_secrets() {
    # Ensure SSL directory permissions are correct
    if [ -d "/tmp/ssl" ]; then
        chmod -R 777 /tmp/ssl || echo "Could not set permissions on /tmp/ssl"
    fi
    
    local token=$(get_token)
    
    if [ -z "$token" ]; then
        echo "❌ Error: No Vault token found"
        return 1
    fi
    
    # Try to retrieve database secrets from the new vault container
    response=$(curl -s -k \
        -H "X-Vault-Token: $token" \
        "https://vault:8200/v1/secret/data/django/database")
    
    # Check if the response contains data
    if echo "$response" | grep -q "\"data\""; then
        echo "✅ Successfully retrieved database secrets from Vault"
        return 0
    else
        echo "❌ Error: Failed to retrieve database secrets"
        echo "Response: $response"
        return 1
    fi
}

# Try to get secrets with retries
while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
    if get_secrets; then
        exit 0
    fi
    
    echo "⏳ Attempt $ATTEMPT of $MAX_ATTEMPTS - Will retry in $RETRY_DELAY seconds..."
    ATTEMPT=$((ATTEMPT + 1))
    sleep $RETRY_DELAY
done

echo "❌ Error: Failed to connect to Vault"
exit 1

# Main function to orchestrate the secrets initialization process
main() {
    echo "⏳ Starting Vault secrets initialization..."
    
    if ! wait_for_vault; then
        echo "❌ Error: Failed to connect to Vault"
        exit 1
    fi

    if ! wait_for_token; then
        echo "❌ Error: Failed to get Vault token"
        exit 1
    fi

    if ! wait_for_secrets; then
        echo "❌ Error: Failed to verify secrets in Vault"
        exit 1
    fi

    if ! get_db_secrets; then
        echo "❌ Error: Failed to get database secrets"
        exit 1
    fi

    # Verify all required secrets are present
    if [ -z "$POSTGRES_DB" ] || [ -z "$POSTGRES_USER" ] || [ -z "$POSTGRES_PASSWORD" ]; then
        echo "❌ Error: Required environment variables not set"
        exit 1
    fi

    echo "✅ All secrets loaded successfully"
    echo "✅ Database configuration complete"
}

main "$@"
