#!/usr/bin/env bash

# Run tests with set -e - exit on error
# set -e

# add adx script to PATH
export PATH=$WORKSPACE/adx_develop/:$PATH
IMAGE_TAG=$(git branch --show-current)
export IMAGE_TAG

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
