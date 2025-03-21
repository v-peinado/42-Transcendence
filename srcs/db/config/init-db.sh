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
#    - Configures SSL for secure connections

# Note: Most database initialization is handled by the official PostgreSQL
# Docker image using environment variables (POSTGRES_USER, POSTGRES_PASSWORD, etc.)

if [ ! -f "${PGDATA}/postgresql.conf" ]; then
    # Basic PostgreSQL configuration
    cat >> "${PGDATA}/postgresql.conf" <<EOF
listen_addresses = '*'

# Checkpoint and Performance tuning
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
ssl_prefer_server_ciphers = on
ssl_min_protocol_version = 'TLSv1.2'
ssl_ca_file = '/var/lib/postgresql/ssl/server.crt'
EOF

    # Copy pg_hba.conf
    cp /tmp/pg_hba.conf "${PGDATA}/pg_hba.conf"
    chmod 600 "${PGDATA}/pg_hba.conf"
    chown postgres:postgres "${PGDATA}/pg_hba.conf"
    
    # Ensure SSL certificate permissions are correct and accessible
    if [ -f "/var/lib/postgresql/ssl/server.crt" ] && [ -f "/var/lib/postgresql/ssl/server.key" ]; then
        echo "SSL certificates found at correct location"
        ls -la /var/lib/postgresql/ssl/
    else
        echo "WARNING: Copying SSL certificates from temp location..."
        mkdir -p /var/lib/postgresql/ssl
        if [ -f "/tmp/ssl/transcendence.crt" ] && [ -f "/tmp/ssl/transcendence.key" ]; then
            cp /tmp/ssl/transcendence.crt /var/lib/postgresql/ssl/server.crt
            cp /tmp/ssl/transcendence.key /var/lib/postgresql/ssl/server.key
            chmod 600 /var/lib/postgresql/ssl/server.key
            chmod 644 /var/lib/postgresql/ssl/server.crt
            chown postgres:postgres /var/lib/postgresql/ssl/server.crt /var/lib/postgresql/ssl/server.key
            echo "Certificates copied successfully"
        else
            echo "ERROR: SSL certificates not found at /tmp/ssl/"
            ls -la /tmp/ssl/ || echo "Directory does not exist"
        fi
    fi
fi

# Add an extra check to verify SSL configuration after initialization
echo "Verifying PostgreSQL SSL configuration..."
if [ -f "/var/lib/postgresql/ssl/server.crt" ] && [ -f "/var/lib/postgresql/ssl/server.key" ]; then
    echo "SSL certificate files exist."
else
    echo "ERROR: SSL certificate files missing. Creating empty placeholders to prevent startup errors."
    mkdir -p /var/lib/postgresql/ssl
    touch /var/lib/postgresql/ssl/server.crt
    touch /var/lib/postgresql/ssl/server.key
    chmod 600 /var/lib/postgresql/ssl/server.key
    chmod 644 /var/lib/postgresql/ssl/server.crt
    chown postgres:postgres /var/lib/postgresql/ssl/server.crt /var/lib/postgresql/ssl/server.key
fi
