pnsppusr/bin/env bash

echo "Docker cleanup"
docker-compose down --rmi all -v --remove-orphans

echo "Preparing environment"
cd ../
export PATH=$WORKSPACE/adx_develop/:$PATH
yes | adx setup
#if [ ! -e "$(dirname "${PWD}")"/datapusher ]; then
#  ln -s "${PWD}"/datapusher "$(dirname "${PWD}")"/datapusher
#fi
#if [ ! -e "$(dirname "${PWD}")"/ckan ]; then
#  ln -s "${PWD}"/ckan "$(dirname "${PWD}")"/ckan
#fi
#if [ ! -e "$(dirname "${PWD}")"/adx_develop ]; then
#  ln -s "${PWD}" "$(dirname "${PWD}")"/adx_develop
#fi

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
adx test ytp-request


#echo "Cleanup"
#rm -f "$(dirname "${PWD}")"/datapusher
#rm -f "$(dirname "${PWD}")"/ckan
#rm -f "$(dirname "${PWD}")"/adx_develop
