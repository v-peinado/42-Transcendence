#!/bin/bash
set -e

# Run setup script only once
/usr/local/bin/setup.sh

# Execute the official postgres entrypoint script
exec docker-entrypoint.sh postgres "$@"
