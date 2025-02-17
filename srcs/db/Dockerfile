FROM postgres:17

# Copy scripts and config files
COPY setup.sh /usr/local/bin/
COPY init-db.sh /docker-entrypoint-initdb.d/
COPY pg_hba.conf /docker-entrypoint-initdb.d/

# Set execute permissions and prepare data directory
RUN chmod +x /usr/local/bin/setup.sh \
    && chmod +x /docker-entrypoint-initdb.d/init-db.sh \
    && mkdir -p /var/lib/postgresql/data

# Let PostgreSQL handle user permissions
