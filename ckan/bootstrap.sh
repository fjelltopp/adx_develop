#!/bin/sh
export WORKON_HOME="/usr/lib/ckan/.adxvenv"
export XDG_CACHE_HOME="/usr/lib/ckan/.adxvenv/cache"
export CKAN_HOME=/usr/lib/ckan
export CKAN_VENV=$CKAN_HOME/venv
export CKAN_CONFIG=/etc/ckan
export CKAN_STORAGE_PATH=/var/lib/ckan
export PATH=${CKAN_VENV}/bin:${PATH}

cd /usr/lib/ckan/ && mkdir .adxvenv
cd /usr/lib/adx/adx_develop/
rm -rf /usr/lib/adx/ckan/ckan/pastertemplates/template/ckanext_+project_shortname+.egg-info
export HOME=/usr/lib/ckan/
pipenv sync --dev
echo "show current dir"
ls -la
echo "Show local/bin"
ls -la /usr/local/bin
echo "Show env vars"
export
cd "$HOME"
rm -rf venv;
if [ ! -L venv ]; then
  ln -s .adxvenv/adx_develop-YYZTJvBg venv
fi
if [ ! -L /usr/local/bin/ckan ]; then
  ln -s "$HOME"/venv/bin/ckan /usr/local/bin/ckan
fi
if [ ! -L /usr/local/bin/ckan-paster ]; then
  ln -s "$HOME"/venv/bin/paster /usr/local/bin/ckan-paster
fi
if [ ! -L /usr/local/bin/ckan-pytest ]; then
  ln -s "$HOME"/venv/bin/pytest /usr/local/bin/ckan-pytest
fi
# chown -R ckan:ckan ./
