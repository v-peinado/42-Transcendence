#!/bin/bash
set -e

echo "Starting PostgreSQL initialization..."

# Configure PostgreSQL settings
cat >> "${PGDATA}/postgresql.conf" <<EOF

# Custom configuration
listen_addresses = '*'
max_connections = 100

# Memory settings
shared_buffers = 128MB
work_mem = 4MB
maintenance_work_mem = 64MB

# Query tuning
random_page_cost = 1.1
effective_cache_size = 384MB

# Logging
log_min_duration_statement = 1000
log_statement = 'none'
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '
EOF

# Wait for PostgreSQL to start
until pg_isready -q; do
    sleep 1
done

# Create database and user
psql -v ON_ERROR_STOP=1 --username "${POSTGRES_USER}" --dbname "postgres" --no-align --tuples-only <<-EOSQL
    -- Create application database
    CREATE DATABASE ${DB_NAME};
    
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '${DB_USER}') THEN
            CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';
        END IF;
    END \$\$;

    -- Grant privileges
    GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};
EOSQL

# Configure database
psql -v ON_ERROR_STOP=1 --username "${POSTGRES_USER}" --dbname "${DB_NAME}" --no-align --tuples-only <<-EOSQL
    -- Grant privileges
    GRANT ALL PRIVILEGES ON SCHEMA public TO ${DB_USER};
EOSQL

# Configure pg_hba.conf
cp /tmp/pg_hba.conf "${PGDATA}/pg_hba.conf"
chmod 600 "${PGDATA}/pg_hba.conf"
chown postgres:postgres "${PGDATA}/pg_hba.conf"

echo "PostgreSQL initialization completed successfully."
