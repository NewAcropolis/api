FROM postgres:9.5

# Allow connections; we don't map out any ports so only linked docker containers can connect
RUN echo "host all  all    0.0.0.0/0  md5" >> /var/lib/postgresql/data/pg_hba.conf

# Customize default user/pass/db
# ENV POSTGRES_DB na_api
# ENV POSTGRES_USER na_api

COPY docker/initdb.sql /docker-entrypoint-initdb.d/