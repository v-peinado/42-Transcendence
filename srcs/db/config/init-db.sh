#!/bin/bash
set -e

# Check if data directory already contains files
if [ "$(ls -A /var/lib/postgresql/data)" ]; then
    echo "Data directory already contains a database. No changes will be made."
    exit 0
fi

# Only create and configure if directory is empty
mkdir -p /var/lib/postgresql/data
chown postgres:postgres /var/lib/postgresql/data
chmod 700 /var/lib/postgresql/data

echo "Data directory initialized successfully."

# Create postgres superuser
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE USER postgres WITH SUPERUSER PASSWORD '${POSTGRES_PASSWORD}';
    ALTER USER postgres WITH LOGIN;
EOSQL

echo "PostgreSQL user 'postgres' created successfully."
