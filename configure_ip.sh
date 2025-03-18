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

# Check if the .env file exists
if [ ! -f "$ENV_FILE" ]; then
    echo "Error: .env file not found at $ENV_FILE"
    exit 1
fi

# Extract current IP_SERVER value from .env file
CURRENT_IP=$(grep -o "IP_SERVER=.*" "$ENV_FILE" | cut -d'=' -f2)
echo "Current IP_SERVER setting: $CURRENT_IP"

# If script is run without arguments and current IP is not localhost, reset to localhost
if [ -z "$1" ] && [ "$CURRENT_IP" != "localhost" ]; then
    echo "Resetting IP_SERVER to 'localhost' (no argument provided and current IP is not localhost)"
    IP_ADDRESS="localhost"
else
    # Use manual IP if provided as argument
    if [ -n "$1" ]; then
        IP_ADDRESS="$1"
        echo "Using manual IP address: $IP_ADDRESS"
    else
        # Otherwise detect IP
        echo "Detecting IP address..."
        # Capture just the IP address
        IP_ADDRESS=$(detect_lan_ip)
        echo "Detected IP address: $IP_ADDRESS"
    fi
fi

# Check if we have a valid IP
if [ "$IP_ADDRESS" = "localhost" ]; then
    echo "Using 'localhost' as IP_SERVER value."
    echo "Only this machine will be able to connect to the application."
else
    # Additional IP validation could go here
    echo "Using IP address: $IP_ADDRESS"
fi

echo "Updating IP_SERVER in .env file to: $IP_ADDRESS"

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
echo "IP Configuration Behavior:"
echo "- Running './configure_ip.sh' with no arguments:"
echo "  * If current IP is 'localhost': Will attempt to detect and set your LAN IP."
echo "  * If current IP is not 'localhost': Will reset back to 'localhost'."
echo "- Running './configure_ip.sh <ip_address>': Will always set to specified IP."
echo ""
echo "Don't forget to:"
echo "1. Update your 42 OAuth app Redirect URI to: https://$IP_ADDRESS:8445/login/"
echo "2. Restart containers: docker-compose down && docker-compose up -d"
echo "=================================================="
