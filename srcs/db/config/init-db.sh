#!/bin/bash
set -e

echo "Starting PostgreSQL initialization..."

# Basic PostgreSQL configuration
cat >> "${PGDATA}/postgresql.conf" <<EOF
listen_addresses = '*'
EOF

# Copy pg_hba.conf
cp /tmp/pg_hba.conf "${PGDATA}/pg_hba.conf"
chmod 600 "${PGDATA}/pg_hba.conf"
chown postgres:postgres "${PGDATA}/pg_hba.conf"

# Create database and user using POSTGRES_USER from env
psql -U "${POSTGRES_USER}" --dbname template1 <<-EOSQL
    -- Create user if not exists
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '${POSTGRES_USER}') THEN
            CREATE USER ${POSTGRES_USER} WITH PASSWORD '${POSTGRES_PASSWORD}' SUPERUSER;
        END IF;
    END \$\$;

    -- Create database if not exists
    SELECT 'CREATE DATABASE ${POSTGRES_DB} OWNER ${POSTGRES_USER}'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '${POSTGRES_DB}');
EOSQL

echo "PostgreSQL initialization completed successfully."
