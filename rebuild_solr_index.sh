#!/usr/bin/env bash
# Rebuild the CKAN Solr search index inside the running ckan container.
# Run this from the repo root after a stack restart to make all datasets visible.
#
# Usage: ./rebuild_solr_index.sh

set -e

CONTAINER="ckan"
CONFIG="/etc/ckan/ckan.ini"

echo "Rebuilding Solr search index in container '${CONTAINER}'..."
docker exec "${CONTAINER}" /usr/local/bin/ckan --config="${CONFIG}" search-index rebuild
echo "Done. Solr index rebuilt successfully."
