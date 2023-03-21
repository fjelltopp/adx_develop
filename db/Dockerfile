# FROM postgres:9.6
# FROM mdillon/postgis:11
FROM postgres:12-bullseye
# FROM postgis/postgis:12-3.3
MAINTAINER Fjelltopp

# after https://github.com/postgis/docker-postgis/blob/master/12-3.3/Dockerfile
ENV POSTGIS_VERSION 3.3.2+dfsg-1.pgdg110+1

RUN apt-get update \
      && apt-cache showpkg postgresql-$PG_MAJOR-postgis-$POSTGIS_MAJOR \
      && apt-get install -y --no-install-recommends \
           # ca-certificates: for accessing remote raster files;
           #   fix: https://github.com/postgis/docker-postgis/issues/307
           ca-certificates \
           \
           postgresql-$PG_MAJOR-postgis-$POSTGIS_MAJOR=$POSTGIS_VERSION \
           postgresql-$PG_MAJOR-postgis-$POSTGIS_MAJOR-scripts \
      && rm -rf /var/lib/apt/lists/*
# RUN echo "host all  all    0.0.0.0/0  md5" >> /var/lib/postgresql/data/pg_hba.conf

# Customize default user/pass/db
ENV POSTGRES_DB ckan
ENV POSTGRES_USER ckan
ARG POSTGRES_PASSWORD
ARG DS_RO_PASS

# Include datastore setup scripts
ADD ./docker-entrypoint-initdb.d /docker-entrypoint-initdb.d
