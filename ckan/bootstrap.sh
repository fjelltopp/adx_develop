#!/bin/bash

set -e

export CKAN_HOME=/usr/lib/adx
export WORKON_HOME="$CKAN_HOME/.adxvenv"
export XDG_CACHE_HOME="$CKAN_HOME/.adxvenv/cache"
export CKAN_VENV=$CKAN_HOME/venv
export CKAN_CONFIG=/etc/ckan
export CKAN_STORAGE_PATH="$CKAN_HOME"
export PATH=${CKAN_VENV}/bin:${PATH}
export HOME="$CKAN_HOME"

cd "$CKAN_HOME" 
if [ ! -d .adxvenv  ]; then
  mkdir .adxvenv
fi
# The rm command below is a workaround for building the current 2.9.* version of CKAN with pipenv
rm -rf /usr/lib/adx/submodules/ckan/ckan/pastertemplates/template/ckanext_+project_shortname+.egg-info
cd /usr/lib/adx/ || exit 1
pipenv sync --dev
pipenv run python -m pip install --no-warn-conflicts jinja2==2.11
echo "installed python packages"
pipenv run python -m pip freeze
echo "show current dir"
ls -la
echo "Show local/bin"
ls -la /usr/local/bin
echo "Show env vars"
export
cd "$HOME" || exit 1
rm -rf venv;
if [ ! -L venv ]; then
  ln -s .adxvenv/adx* venv
fi
if [ ! -L .venv ]; then
    ln -s venv .venv
fi
if [ ! -L /usr/local/bin/ckan ]; then
  ln -s "$HOME"/venv/bin/ckan /usr/local/bin/ckan
fi
if [ ! -L /usr/local/bin/ckan-pytest ]; then
  ln -s "$HOME"/venv/bin/pytest /usr/local/bin/ckan-pytest
fi
