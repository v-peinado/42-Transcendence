#!/bin/bash

# This script fixes permissions for shared volumes between containers
# Run it before starting the containers

VOLUME_DIR="/tmp/ssl_volume"

# Create volume directory if it doesn't exist
mkdir -p "$VOLUME_DIR"

# Set proper permissions
chmod -R 777 "$VOLUME_DIR"

echo "Permissions for $VOLUME_DIR have been set to 777"
