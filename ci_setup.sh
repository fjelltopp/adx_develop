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

