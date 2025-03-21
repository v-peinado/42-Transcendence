FROM postgres:17

# Install required tools
RUN apt-get update && apt-get install -y \
	curl \
	jq \
	openssl \
	ca-certificates \
	ssl-cert \
	&& rm -rf /var/lib/apt/lists/*

# Add postgres user to ssl-cert group for certificate access
RUN usermod -a -G ssl-cert postgres

# Set PostgreSQL initialization parameters
ENV POSTGRES_INITDB_ARGS="--auth-local=md5 --auth-host=md5"

# Copy config files and scripts
COPY config/init-db.sh /docker-entrypoint-initdb.d/
COPY config/pg_hba.conf /tmp/
COPY config/get-vault-secrets.sh /usr/local/bin/
COPY diagnose-ssl.sh /usr/local/bin/
COPY postgresql-ssl-enabler.sh /usr/local/bin/

# Set permissions
RUN chmod 755 /docker-entrypoint-initdb.d/init-db.sh && \
	chmod 755 /usr/local/bin/get-vault-secrets.sh && \
	chmod 755 /usr/local/bin/diagnose-ssl.sh && \
	chmod 755 /usr/local/bin/postgresql-ssl-enabler.sh && \
	chown -R postgres:postgres /docker-entrypoint-initdb.d/
