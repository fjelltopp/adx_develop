#!/bin/sh
export CKAN_HOME=/usr/lib/adx_develop
export WORKON_HOME="$CKAN_HOME/.adxvenv"
export XDG_CACHE_HOME="$CKAN_HOME/.adxvenv/cache"
export CKAN_VENV=$CKAN_HOME/venv
export CKAN_CONFIG=/etc/ckan
export CKAN_STORAGE_PATH="$CKAN_HOME"
export PATH=${CKAN_VENV}/bin:${PATH}
export HOME="$CKAN_HOME"

cd "$CKAN_HOME" && mkdir .adxvenv
# The rm command below is a workaround for building the current 2.9.* version of CKAN with pipenv
rm -rf /usr/lib/adx/ckan/ckan/pastertemplates/template/ckanext_+project_shortname+.egg-info
cd /usr/lib/adx/adx_develop
pipenv sync --dev
echo "show current dir"
ls -la
echo "Show local/bin"
ls -la /usr/local/bin
echo "Show env vars"
export
cd "$HOME" || exit 1
rm -rf venv;
if [ ! -L venv ]; then
  ln -s .adxvenv/adx_develop-YYZTJvBg venv
fi
if [ ! -L /usr/local/bin/ckan ]; then
  ln -s "$HOME"/venv/bin/ckan /usr/local/bin/ckan
fi
if [ ! -L /usr/local/bin/ckan-pytest ]; then
  ln -s "$HOME"/venv/bin/pytest /usr/local/bin/ckan-pytest
fi
