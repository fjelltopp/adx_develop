FROM ckan/ckan:latest
USER root

# Install dev requirements
RUN ckan-pip install -r /usr/lib/ckan/venv/src/ckan/dev-requirements.txt &&\
    ckan-pip install ckanapi

# Install all extensions with a remote source
RUN ckan-pip install -e "git+https://github.com/ckan/ckanext-spatial.git#egg=ckanext-spatial" && ckan-pip install -r /usr/lib/ckan/venv/src/ckanext-spatial/pip-requirements.txt
RUN ckan-pip install -e "git+https://github.com/ckan/ckanext-geoview.git#egg=ckanext-geoview" && ckan-pip install -r /usr/lib/ckan/venv/src/ckanext-geoview/pip-requirements.txt
RUN ckan-pip install -e "git+https://github.com/EnviDat/ckanext-composite.git#egg=ckanext-composite"
RUN ckan-pip install -e "git+https://github.com/open-data/ckanext-repeating.git#egg=ckanext-repeating"



# Install requirements for extensions with a local source
COPY ./ckanext-validator/requirements.txt /usr/lib/ckan/validator-req.txt
RUN ckan-pip install -r /usr/lib/ckan/validator-req.txt && \
    rm /usr/lib/ckan/validator-req.txt

# Configs
COPY ./adx_develop/ckan/ckan-entrypoint-adx.sh /ckan-entrypoint.sh
COPY ./adx_develop/ckan/adx_config.ini /etc/ckan/production.ini
