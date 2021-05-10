#!/usr/bin/env bash

# Remove all containers and volumes
echo "Docker cleanup"
docker-compose down --rmi all -v --remove-orphans

if [ -v "$CHANGE_ID" ]
then
  BRANCH="origin/pr/$CHANGE_ID"
else 
  BRANCH="$GIT_BRANCH"
fi

echo "Preparing environment"
cd ../
# add adx script to PATH
export PATH=$WORKSPACE/adx_develop/:$PATH
# prepare environment
cp "$WORKSPACE"/adx_develop/dev.env "$WORKSPACE"/adx_develop/.env
# Setup environment
yes | adx setup
git fetch origin +refs/pull/*/merge:refs/remotes/origin/pr/* && git checkout "${BRANCH}"
cd "$WORKSPACE"/adx_develop/ && git fetch origin +refs/pull/*/merge:refs/remotes/origin/pr/* && git checkout "${BRANCH}" 
cd "$WORKSPACE" || exit
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

