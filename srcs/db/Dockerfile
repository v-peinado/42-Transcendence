FROM postgres:17

# Set PostgreSQL initialization parameters
ENV POSTGRES_INITDB_ARGS="--auth-local=md5 --auth-host=md5"

# Copy config files
COPY config/init-db.sh /docker-entrypoint-initdb.d/
COPY config/pg_hba.conf /tmp/

# Set permissions
RUN chmod 755 /docker-entrypoint-initdb.d/init-db.sh && \
	chown -R postgres:postgres /docker-entrypoint-initdb.d/
