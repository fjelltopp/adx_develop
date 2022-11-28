#FROM postgres:9.6
FROM mdillon/postgis:11
MAINTAINER Fjelltopp

# Customize default user/pass/db
ENV POSTGRES_DB ckan
ENV POSTGRES_USER ckan
ARG POSTGRES_PASSWORD
ARG DS_RO_PASS

# Include datastore setup scripts
ADD ./docker-entrypoint-initdb.d /docker-entrypoint-initdb.d
