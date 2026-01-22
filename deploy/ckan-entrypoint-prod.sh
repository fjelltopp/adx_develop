#!/bin/bash
set -e

# URL for the primary database, in the format expected by sqlalchemy
: "${CKAN_SQLALCHEMY_URL:=}"
: "${CKAN_SOLR_URL:=}"
: "${CKAN_REDIS_URL:=}"
: "${CKAN_DATAPUSHER_URL:=}"

export CKAN_HOME=/usr/lib/adx
export CKAN_VENV=$CKAN_HOME/venv
export PATH=${CKAN_VENV}/bin:${PATH}

# Combine base config with secrets using Python ConfigParser
# secrets.ini values override production.ini
echo "Combining configuration files..."
python3 << 'PYEOF'
import configparser
import sys

config = configparser.ConfigParser()
config.read('/etc/ckan/production.ini')
config.read('/etc/ckan/secrets.ini')  # Later values override earlier

with open('/tmp/ckan.ini', 'w') as f:
    config.write(f)
PYEOF
export CONFIG="/tmp/ckan.ini"
export CKAN_INI="/tmp/ckan.ini"

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
  if [ -n "${ADR_CKAN_SAML_IDP_CERT}" ]; then
    echo "${ADR_CKAN_SAML_IDP_CERT}" > /tmp/saml_idp.crt || echo "Warning: Could not write SAML IDP cert"
  fi
}

# Validate required environment variables
if [ -z "$CKAN_SQLALCHEMY_URL" ]; then
  abort "ERROR: no CKAN_SQLALCHEMY_URL specified"
fi

if [ -z "$CKAN_SOLR_URL" ]; then
    abort "ERROR: no CKAN_SOLR_URL specified"
fi

if [ -z "$CKAN_REDIS_URL" ]; then
    abort "ERROR: no CKAN_REDIS_URL specified"
fi

if [ -z "$CKAN_DATAPUSHER_URL" ]; then
    abort "ERROR: no CKAN_DATAPUSHER_URL specified"
fi

set_environment
echo "CKAN production environment ready"

# Initialize CKAN database and run plugin migrations
echo "Initializing CKAN database..."
ckan --config="$CONFIG" db init || echo "CKAN database already initialized"

echo "Setting up DataStore permissions..."
ckan --config="$CONFIG" datastore set-permissions | psql "${CKAN_DATASTORE_WRITE_URL}" || echo "Warning: DataStore set-permissions failed or already applied"

echo "Running database migrations for plugins..."
ckan --config="$CONFIG" db upgrade -p pages || echo "Warning: ckanext-pages migration failed or already applied"
# ckan --config="$CONFIG" versions initdb || echo "Warning: ckanext-versions initdb failed or already applied"
# ckan --config="$CONFIG" validation init-db || echo "Warning: ckanext-validation init-db failed or already applied"
ckan --config="$CONFIG" unaids initdb || echo "Warning: ckanext-unaids initdb failed or already applied"

exec "$@"
