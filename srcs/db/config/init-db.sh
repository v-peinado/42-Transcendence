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

# Checkpoint and Performance tuning
checkpoint_timeout = 300
checkpoint_completion_target = 0.9
checkpoint_warning = 30s
max_wal_size = 1GB
min_wal_size = 80MB
effective_cache_size = 1GB
maintenance_work_mem = 128MB
EOF

    # Copy pg_hba.conf
    cp /tmp/pg_hba.conf "${PGDATA}/pg_hba.conf"
    chmod 600 "${PGDATA}/pg_hba.conf"
    chown postgres:postgres "${PGDATA}/pg_hba.conf"
fi
