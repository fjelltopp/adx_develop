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


error(){
  echo "CKAN ${1} test did fail, check logs"
  return 1
}


run_adx_test(){
  echo "Running tests for CKAN ${1}"
  adx test "${1}"
  retVal=$?
  echo "Exit code: ${retVal}"
  if [ ${retVal} -ne 0 ]; then
    error "${1}"
  fi
}

tests="restricted dhis2harvester emailasusername file_uploader_ui pages pdfview scheming validation ytp-request unaids"

for test in ${tests}
  do run_adx_test "${test}"
done

echo "Docker cleanup"
docker-compose down --rmi all -v --remove-orphans
