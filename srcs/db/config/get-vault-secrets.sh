#!/bin/bash

set -e  # Exit on error

MAX_ATTEMPTS=45
ATTEMPT=1
RETRY_DELAY=5

# Get the token from the file to obtain secrets in Vault
get_token() {
    if [ -f "/tmp/ssl/django_token" ]; then
        cat "/tmp/ssl/django_token"
    else
        echo ""
    fi
}

# Get secrets from Vault
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
