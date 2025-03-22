#!/bin/bash

# WAF service entrypoint script
# This script:
# 1. Waits for SSL certificates to be available
# 2. Substitutes environment variables in nginx configuration
# 3. Starts nginx in foreground mode

set -e

# Color definitions for messages
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Log function for better output formatting
log() {
    echo -e "${GREEN}[WAF]${NC} $1"
}

log "Starting WAF service..."

# Wait for SSL certificates to be available
log "Checking for SSL certificates..."
until [ -f /tmp/ssl/transcendence.crt ] && [ -f /tmp/ssl/transcendence.key ]; do 
    echo -e "${YELLOW}Waiting for SSL certificates...${NC}"
    sleep 2
done

log "SSL certificates found!"

# Template substitution for nginx configuration
log "Configuring nginx with environment variables..."
envsubst '$$IP_SERVER' < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf

# Start nginx in foreground mode
log "Starting nginx in foreground mode..."
exec nginx -g 'daemon off;'
