#!/usr/bin/env bash


echo "Preparing environment"

yes | ./adx setup
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
./adx build
echo "running ./adx up"
./adx up
echo "tunning ./adx/dbsetup"
./adx dbsetup
echo "running ./adx restart ckan"
./adx restart ckan

echo "Show docker-compose containers"
docker-compose ps
echo "Running ./adx testsetup"
./adx testsetup
echo "Running ./adx test restricted"
./adx test restricted

#echo "Cleanup"
#rm -f "$(dirname "${PWD}")"/datapusher
#rm -f "$(dirname "${PWD}")"/ckan
#rm -f "$(dirname "${PWD}")"/adx_develop
