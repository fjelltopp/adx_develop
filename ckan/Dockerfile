FROM ckan/ckan:latest
USER root

# Install dev requirements
RUN ckan-pip install -r /usr/lib/ckan/venv/src/ckan/dev-requirements.txt

# Install all extensions with a remote source
RUN ckan-pip install -e "git+https://github.com/ckan/ckanext-spatial.git#egg=ckanext-spatial" && ckan-pip install -r /usr/lib/ckan/venv/src/ckanext-spatial/pip-requirements.txt
RUN ckan-pip install -e "git+https://github.com/ckan/ckanext-geoview.git#egg=ckanext-geoview" && ckan-pip install -r /usr/lib/ckan/venv/src/ckanext-geoview/pip-requirements.txt

# Install all extensions with a local source to /usr/lib/adx/
COPY ./ckanext-unaids /usr/lib/adx/ckanext-unaids
RUN ckan-pip install -e /usr/lib/adx/ckanext-unaids
COPY ./ckanext-cloudstorage /usr/lib/adx/ckanext-cloudstorage
RUN ckan-pip install -e /usr/lib/adx/ckanext-cloudstorage

# Configs
COPY ./adx_develop/ckan/ckan-entrypoint-adx.sh /ckan-entrypoint.sh
COPY ./adx_develop/ckan/adx_config.ini /etc/ckan/production.ini

USER ckan
