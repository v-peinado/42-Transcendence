FROM postgres:17

# Set only essential postgres configuration
ENV POSTGRES_INITDB_ARGS="--auth-host=scram-sha-256 --auth-local=trust --data-checksums"

# Copy config files
COPY config/init-db.sh /docker-entrypoint-initdb.d/
COPY config/pg_hba.conf /tmp/

# Set secure permissions and ownership
RUN chmod 755 /docker-entrypoint-initdb.d/init-db.sh && \
	chown -R postgres:postgres /docker-entrypoint-initdb.d/ && \
	chown postgres:postgres /tmp/pg_hba.conf
