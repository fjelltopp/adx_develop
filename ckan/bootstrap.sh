#!/bin/sh
export WORKON_HOME="/usr/lib/ckan/.adxvenv"
export XDG_CACHE_HOME="/usr/lib/ckan/.adxvenv/cache"
cd /usr/lib/ckan/ && mkdir .adxvenv
cd /usr/lib/adx/adx_develop/
export HOME=/usr/lib/ckan/
pipenv sync --dev
ls -la
cd "$HOME"
rm -rf venv;
ln -s .adxvenv/adx_develop-YYZTJvBg venv
ln -s "$HOME"/venv/bin/ckan /usr/local/bin/ckan
ln -s "$HOME"/venv/bin/paster /usr/local/bin/ckan-paster
# chown -R ckan:ckan ./
