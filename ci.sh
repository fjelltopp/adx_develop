#!/usr/bin/env bash

# Remove all containers and volumes
echo "Docker cleanup"
docker-compose down --rmi all -v --remove-orphans

echo "Preparing environment"
cd ../
# add adx script to PATH
export PATH=$WORKSPACE/adx_develop/:$PATH
# Setup environment
yes | adx setup

echo "running ./adx build"
adx build
echo "running ./adx up"
adx up
echo "tunning ./adx/dbsetup"
adx dbsetup
echo "running ./adx restart ckan"
adx restart ckan
echo "Show docker-compose containers"
docker-compose ps
echo "Running ./adx testsetup"
adx testsetup

# Run tests with set -e - exit on error
set -e
echo "Run ckan core tests"
docker exec -it ckan ckan-nosetests --ckan --with-pylons=/usr/lib/ckan/venv/src/ckan/test-core.ini ckan ckanext
echo "Running ./adx test restricted"
adx test restricted
echo "Running dhis2harvester tests"
adx test dhis2harvester
echo "Running emailasusername tests"
adx test emailasusername
echo "Running file_uploader_ui tests"
adx test file_uploader_ui
echo "Running pages tests"
adx test pages
echo "Running pdfview tests"
adx test pdfview
echo "Running scheming tests"
adx test scheming
echo "Running validation tests"
adx test validation
echo "Running ytp-request tests"
adx test ytp-requesta
echo "Running unaids tests"
adx test unaids

