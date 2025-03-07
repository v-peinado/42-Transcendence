#!/bin/bash

# This script detects the LAN IP address and updates the IP_SERVER in .env
# Works on both macOS and Linux environments

ENV_FILE="srcs/.env"

# Function to detect LAN IP address - returns ONLY the IP address, no debug messages
detect_lan_ip() {
    local found_ip=""
    
    # macOS specific methods
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # Try en0 (usually wifi on macOS)
        if found_ip=$(ipconfig getifaddr en0 2>/dev/null); then
            echo "$found_ip"
            return 0
        fi
        
        # Try en1 (other interface on macOS)
        if found_ip=$(ipconfig getifaddr en1 2>/dev/null); then
            echo "$found_ip"
            return 0
        fi
    else
        # Linux methods
        # Try hostname -I (Linux only) and take first IP
        if command -v hostname >/dev/null 2>&1; then
            found_ip=$(hostname -I 2>/dev/null | awk '{print $1}')
            if [[ -n "$found_ip" && "$found_ip" != "127.0.0.1" ]]; then
                echo "$found_ip"
                return 0
            fi
        fi
        
        # Try ip command (modern Linux)
        if command -v ip >/dev/null 2>&1; then
            found_ip=$(ip -4 addr show scope global | grep inet | head -n 1 | awk '{print $2}' | cut -d/ -f1)
            if [[ -n "$found_ip" ]]; then
                echo "$found_ip"
                return 0
            fi
        fi
    fi
    
    # Common fallbacks for both systems
    # Try ifconfig
    if command -v ifconfig >/dev/null 2>&1; then
        # Get first non-localhost inet address
        found_ip=$(ifconfig 2>/dev/null | grep 'inet ' | grep -v '127.0.0.1' | head -n 1 | awk '{print $2}')
        if [[ -n "$found_ip" ]]; then
            # Some systems have the address in $2, others have it as "addr:$2"
            found_ip=${found_ip#addr:}
            echo "$found_ip"
            return 0
        fi
    fi
    
    # No IP found
    echo "localhost"
    return 1
}

echo "Detecting IP address..."
# Capture just the IP address
IP_ADDRESS=$(detect_lan_ip)
echo "Detected IP address: $IP_ADDRESS"

# Use manual IP if provided as argument
if [ -n "$1" ]; then
    IP_ADDRESS="$1"
    echo "Using manual IP address: $IP_ADDRESS"
fi

# Check if we have a valid IP
if [ "$IP_ADDRESS" = "localhost" ]; then
    echo "Failed to detect a valid LAN IP address."
    echo "For connectivity with other devices, you should specify your IP:"
    echo "Example: ./configure_ip.sh 192.168.1.100"
    echo ""
    read -p "Continue with 'localhost'? (only this machine will connect) [y/N]: " choice
    if [[ ! "$choice" =~ ^[yY]$ ]]; then
        echo "Operation cancelled."
        exit 1
    fi
fi

echo "Updating IP_SERVER in .env file to: $IP_ADDRESS"

# Check if .env file exists
if [ ! -f "$ENV_FILE" ]; then
    echo "Error: .env file not found at $ENV_FILE"
    exit 1
fi

# Update the IP_SERVER variable - with correct handling for macOS/Linux
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS requires an empty string with -i
    sed -i '' "s/IP_SERVER=.*/IP_SERVER=$IP_ADDRESS/" "$ENV_FILE"
else
    # Linux version
    sed -i "s/IP_SERVER=.*/IP_SERVER=$IP_ADDRESS/" "$ENV_FILE"
fi

echo ""
echo "=============== IMPORTANT REMINDER ==============="
echo "IP_SERVER has been updated to: $IP_ADDRESS"
if [ "$IP_ADDRESS" != "localhost" ]; then
    echo "✓ Other devices can connect to your application."
else
    echo "⚠️ WARNING: Using 'localhost' - ONLY this machine can connect."
fi

echo ""
echo "Don't forget to:"
echo "1. Update your 42 OAuth app Redirect URI to: https://$IP_ADDRESS:8445/login/"
echo "2. Restart containers: docker-compose down && docker-compose up -d"
echo "=================================================="
