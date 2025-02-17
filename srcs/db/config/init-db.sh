#!/bin/bash
set -e

# Configure PostgreSQL for the first time if needed 
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
