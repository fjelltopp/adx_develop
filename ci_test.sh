#!/usr/bin/env bash

# Run tests with set -e - exit on error
# set -e

# add adx script to PATH
export PATH=$WORKSPACE/adx_develop/:$PATH

# check if custom ckan image should be built
git diff -s --exit-code ./ckan
if [ $? == 1 ]; then
  CKAN_IMAGE_TAG="$CHANGE_BRANCH"
  export CKAN_IMAGE_TAG
fi

error(){
  echo "CKAN ${1} test did fail, check logs, docker output below:"
  echo "*** CKAN container logs start ***"
  sudo docker logs ckan
  echo "*** CKAN container logs end ***"
  return 1
}


run_adx_test(){
  echo "Running tests for CKAN ${1}"
  adx test "${1}" --no-interaction
  retVal=$?
  echo "Exit code: ${retVal}"
  if [ ${retVal} -ne 0 ]; then
    error "${1}"
  fi
}


run_adx_test "${1}"
