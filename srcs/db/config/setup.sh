#!/bin/bash
set -e

# Check if directory exists and is not empty
if [ -d "/var/lib/postgresql/data" ] && [ "$(ls -A /var/lib/postgresql/data)" ]; then
    echo "Data directory already exists and contains data. No changes will be made."
    exit 0
fi

# If it doesn't exist or is empty, create/configure the directory
mkdir -p /var/lib/postgresql/data
chmod 700 /var/lib/postgresql/data
chown postgres:postgres /var/lib/postgresql/data

echo "Data directory created and configured successfully."
exit 0
