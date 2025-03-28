FROM postgres:17

# Install required tools
RUN apt-get update && apt-get install -y \
	curl \
	jq \
	openssl \
	ssl-cert \
	&& rm -rf /var/lib/apt/lists/*

# Postgres user to ssl-cert group for certificate access
RUN usermod -a -G ssl-cert postgres

# Set PostgreSQL initialization parameters
ENV POSTGRES_INITDB_ARGS="--auth-local=md5 --auth-host=md5"

# Copy config files
COPY config/init-db.sh /docker-entrypoint-initdb.d/
COPY config/pg_hba.conf /tmp/
COPY config/get-vault-secrets.sh /usr/local/bin/
COPY entrypoint.sh /usr/local/bin/

# Set permissions
RUN chmod 755 /docker-entrypoint-initdb.d/init-db.sh && \
	chmod 755 /usr/local/bin/get-vault-secrets.sh && \
	chmod 755 /usr/local/bin/entrypoint.sh && \
	chown -R postgres:postgres /docker-entrypoint-initdb.d/ && \
	mkdir -p /var/lib/postgresql/ssl && \
	chmod 755 /var/lib/postgresql/ssl && \
	chown postgres:postgres /var/lib/postgresql/ssl

# Set entrypoint
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
