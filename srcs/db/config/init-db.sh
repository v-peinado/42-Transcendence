#!/bin/bash
set -e

# PostgreSQL Initialization Script

# This script handles the initial configuration of PostgreSQL when the container starts.
# It only runs its configuration if postgresql.conf doesn't exist,
# which allows for persistent configuration across container restarts.

# Key functions:

# 1. Network Configuration:
#    - Sets 'listen_addresses' to '*' to allow connections from all interfaces

# 2. Performance Tuning:
#    - checkpoint_timeout: Time between automatic WAL checkpoints (5 minutes)
#    - checkpoint_completion_target: Spreads checkpoint load over time (90% of interval)
#    - checkpoint_warning: Alerts if checkpoints occur too frequently
#    - max_wal_size: Maximum size for WAL files before forced checkpoint
#    - min_wal_size: Minimum size before WAL files are recycled
#    - effective_cache_size: Estimate of available OS cache
#    - maintenance_work_mem: Memory for maintenance operations

# 3. Security:
#    - Copies pg_hba.conf for access control
#    - Sets appropriate permissions (600) for security
#    - Ensures postgres user owns configuration files

# Note: Most database initialization is handled by the official PostgreSQL
# Docker image using environment variables (POSTGRES_USER, POSTGRES_PASSWORD, etc.)

if [ ! -f "${PGDATA}/postgresql.conf" ]; then
    # Basic PostgreSQL configuration
    cat >> "${PGDATA}/postgresql.conf" <<EOF
listen_addresses = '*'

# Performance tuning
checkpoint_timeout = 300
checkpoint_completion_target = 0.9
checkpoint_warning = 30s
max_wal_size = 1GB
min_wal_size = 80MB
effective_cache_size = 1GB
maintenance_work_mem = 128MB

# SSL Configuration
ssl = on
ssl_cert_file = '/var/lib/postgresql/ssl/server.crt'
ssl_key_file = '/var/lib/postgresql/ssl/server.key'
ssl_ca_file = '/var/lib/postgresql/ssl/server.crt'
ssl_ciphers = 'HIGH:MEDIUM:+3DES:!aNULL'
ssl_min_protocol_version = 'TLSv1.2'
ssl_prefer_server_ciphers = on

# Log only essential connection information
log_connections = on
log_min_messages = warning
log_min_error_statement = error
EOF

    # Copy pg_hba.conf
    cp /tmp/pg_hba.conf "${PGDATA}/pg_hba.conf"
    chmod 600 "${PGDATA}/pg_hba.conf"
    chown postgres:postgres "${PGDATA}/pg_hba.conf"
fi

# Ensure SSL directory exists with proper permissions
if [ ! -d "/var/lib/postgresql/ssl" ]; then
    mkdir -p /var/lib/postgresql/ssl
    echo "Created SSL directory at /var/lib/postgresql/ssl"
fi

# Set proper directory ownership
chown -R postgres:postgres /var/lib/postgresql/ssl 2>/dev/null || echo "Warning: Could not change ownership of SSL directory"

# Copy SSL certificates from shared volume to PostgreSQL directory
if [ -f "/tmp/ssl/transcendence.crt" ] && [ -f "/tmp/ssl/transcendence.key" ]; then
    echo "Found SSL certificates, copying to PostgreSQL directory..."
    cp -f /tmp/ssl/transcendence.crt /var/lib/postgresql/ssl/server.crt
    cp -f /tmp/ssl/transcendence.key /var/lib/postgresql/ssl/server.key
    chmod 600 /var/lib/postgresql/ssl/server.key
    chmod 644 /var/lib/postgresql/ssl/server.crt
    chown postgres:postgres /var/lib/postgresql/ssl/server.crt /var/lib/postgresql/ssl/server.key
    echo "SSL certificates configured successfully"
else
    echo "ERROR: SSL certificates not found in /tmp/ssl/"
fi

# Verify SSL configuration is not duplicated in existing postgresql.conf
if [ -f "${PGDATA}/postgresql.conf" ]; then
    # Create a clean SSL configuration section only if needed
    if ! grep -q "^ssl = on" "${PGDATA}/postgresql.conf"; then
        echo "Adding SSL configuration to postgresql.conf..."
        cat >> "${PGDATA}/postgresql.conf" <<EOF

# SSL Configuration - Added $(date)
ssl = on
ssl_cert_file = '/var/lib/postgresql/ssl/server.crt'
ssl_key_file = '/var/lib/postgresql/ssl/server.key'
ssl_ca_file = '/var/lib/postgresql/ssl/server.crt'
ssl_ciphers = 'HIGH:MEDIUM:+3DES:!aNULL'
EOF
    fi
fi
