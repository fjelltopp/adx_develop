#!/usr/bin/env bash

# Remove all containers and volumes
echo "Docker cleanup"
docker-compose down --rmi all -v --remove-orphans
sudo docker volume prune -f

if [ -v "$CHANGE_ID" ]
then
  BRANCH="$GIT_BRANCH"
else 
  BRANCH="origin/pr/$CHANGE_ID"
fi
echo "CHANGE_ID: ${CHANGE_ID}" 

IMAGE_TAG=$(git branch --show-current)
export IMAGE_TAG
echo "IMAGE_TAG: ${IMAGE_TAG}"

echo "Preparing environment"
cd ../
# add adx script to PATH
export PATH=$WORKSPACE/adx_develop/:$PATH
# disable db restart during test setup
export SKIP_DB_RESTART=True
# prepare environment
cp "$WORKSPACE"/adx_develop/dev.env "$WORKSPACE"/adx_develop/.env
# Init submodules
adx init
# Setup environment
yes | adx setup
git fetch origin +refs/pull/*/merge:refs/remotes/origin/pr/* && git checkout "${BRANCH}"
cd "$WORKSPACE"/adx_develop/ && git fetch origin +refs/pull/*/merge:refs/remotes/origin/pr/* && git checkout "${BRANCH}" 
cd "$WORKSPACE" || exit
echo "running ./adx build"
adx build
echo "running ./adx up"
adx up
echo "Running ./adx testsetup"
adx testsetup
echo "Show docker-compose containers"
adx dc ps

echo "Waiting for CKAN container"
counter=0
while ! docker logs ckan |grep 'CKAN bootstrapping finished, environment ready'; 
  do
    ((counter=counter+1))
    if [ $counter -ge 80 ]; then
      echo "This is taking too long, break!"
      echo "Some logs first:"
      echo "CKAN container logs:"
      docker logs ckan
      echo "DB container logs:"
      docker logs db
      echo "List of containers:"
      adx dc ps
      exit 1
    fi
    echo "Bootstraping not finished, pass $counter"
    sleep 10
  done
