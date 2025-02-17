FROM postgres:17

# Copy config files
COPY config/init-db.sh /docker-entrypoint-initdb.d/
COPY config/pg_hba.conf /tmp/

# Set permissions
RUN chmod 755 /docker-entrypoint-initdb.d/init-db.sh && \
	chown -R postgres:postgres /docker-entrypoint-initdb.d/
