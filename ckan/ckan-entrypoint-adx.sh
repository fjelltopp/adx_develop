#!/bin/sh
set -e

# URL for the primary database, in the format expected by sqlalchemy (required
# unless linked to a container called 'db')
: ${CKAN_SQLALCHEMY_URL:=}
# URL for solr (required unless linked to a container called 'solr')
: ${CKAN_SOLR_URL:=}
# URL for redis (required unless linked to a container called 'redis')
: ${CKAN_REDIS_URL:=}
# URL for datapusher (required unless linked to a container called 'datapusher')
: ${CKAN_DATAPUSHER_URL:=}

CONFIG="${CKAN_CONFIG}/ckan.ini"
/bootstrap.sh

abort () {
  echo "$@" >&2
  exit 1
}

set_environment () {
  export CKAN_SITE_ID=${CKAN_SITE_ID}
  export CKAN_SITE_URL=${CKAN_SITE_URL}
  export CKAN_SQLALCHEMY_URL=${CKAN_SQLALCHEMY_URL}
  export CKAN_SOLR_URL=${CKAN_SOLR_URL}
  export CKAN_REDIS_URL=${CKAN_REDIS_URL}
  export CKAN_STORAGE_PATH=/var/lib/ckan
  export CKAN_DATAPUSHER_URL=${CKAN_DATAPUSHER_URL}
  export CKAN_DATASTORE_WRITE_URL=${CKAN_DATASTORE_WRITE_URL}
  export CKAN_DATASTORE_READ_URL=${CKAN_DATASTORE_READ_URL}
  export CKAN_SMTP_SERVER=${CKAN_SMTP_SERVER}
  export CKAN_SMTP_STARTTLS=${CKAN_SMTP_STARTTLS}
  export CKAN_SMTP_USER=${CKAN_SMTP_USER}
  export CKAN_SMTP_PASSWORD=${CKAN_SMTP_PASSWORD}
  export CKAN_SMTP_MAIL_FROM=${CKAN_SMTP_MAIL_FROM}
  export CKAN_MAX_UPLOAD_SIZE_MB=${CKAN_MAX_UPLOAD_SIZE_MB}
}

write_config () {
  paster make-config --no-interactive ckan "$CONFIG"
}

# If we don't already have a config file, bootstrap
if [ ! -e "$CONFIG" ]; then
  write_config
fi

# Get or create CKAN_SQLALCHEMY_URL
if [ -z "$CKAN_SQLALCHEMY_URL" ]; then
  abort "ERROR: no CKAN_SQLALCHEMY_URL specified in docker-compose.yml"
fi

if [ -z "$CKAN_SOLR_URL" ]; then
    abort "ERROR: no CKAN_SOLR_URL specified in docker-compose.yml"
fi

if [ -z "$CKAN_REDIS_URL" ]; then
    abort "ERROR: no CKAN_REDIS_URL specified in docker-compose.yml"
fi

if [ -z "$CKAN_DATAPUSHER_URL" ]; then
    abort "ERROR: no CKAN_DATAPUSHER_URL specified in docker-compose.yml"
fi

# build js components & allow editing
echo "Starting yarn build"
yarn --cwd /usr/lib/adx/ckanext-unaids/ckanext/unaids/react/
yarn --cwd /usr/lib/adx/ckanext-unaids/ckanext/unaids/react/ build
chmod -R 777 /usr/lib/adx/ckanext-unaids/ckanext/unaids/assets/build

# All steps below are also performed by Datapusher, it's not needed here
# echo "Initialize CKAN db"
# set_environment
# echo "db init..."
# ckan  --config "${CKAN_CONFIG}/ckan.ini" db init
# echo "validation init..."
# paster --plugin=ckanext-validation validation init-db --config "${CKAN_CONFIG}/ckan.ini"
# echo "unaids init..."
# ckan --config "${CKAN_CONFIG}/ckan.ini" unaids initdb
# echo "versions init..."
# ckan  --config "${CKAN_CONFIG}/ckan.ini" versions initdb
# echo "pages init..."
# ckan  --config "${CKAN_CONFIG}/ckan.ini" pages initdb

echo "CKAN bootstrapping finished, environment ready"

exec "$@"
