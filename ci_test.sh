#!/usr/bin/env bash

# Run tests with set -e - exit on error
set -e

# add adx script to PATH
export PATH=$WORKSPACE/adx_develop/:$PATH

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


run_adx_test "${1}"
