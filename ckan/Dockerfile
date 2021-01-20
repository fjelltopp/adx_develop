# See CKAN docs on installation from Docker Compose on usage
FROM python:3.8
MAINTAINER Open Knowledge

## Install required system packages
RUN apt-get -q -y update \
    && apt-get -q -y install \
        supervisor \
        jq \
    && apt-get -q clean \
    && rm -rf /var/lib/apt/lists/*

# Define environment variables
ENV CKAN_HOME /usr/lib/ckan
ENV CKAN_VENV $CKAN_HOME/venv
ENV CKAN_CONFIG /etc/ckan
ENV CKAN_STORAGE_PATH=/var/lib/ckan

# Build-time variables specified by docker-compose.yml / .env
ARG CKAN_SITE_URL

# Create ckan user
RUN useradd -r -u 900 -m -c "ckan account" -d $CKAN_HOME -s /bin/false ckan

# Setup virtual environment for CKAN
RUN mkdir -p $CKAN_VENV $CKAN_CONFIG $CKAN_STORAGE_PATH && \
    python3 -m venv $CKAN_VENV && \
    ln -s $CKAN_VENV/bin/pip /usr/local/bin/ckan-pip &&\
    ln -s $CKAN_VENV/bin/ckan /usr/local/bin/ckan &&\
    ln -s $CKAN_VENV/bin/python /usr/local/bin/ckan-python &&\
	  ln -s $CKAN_VENV/bin/pytest /usr/local/bin/ckan-pytest &&\
    echo "alias cdckanext='cd /usr/lib/adx/'" >> $HOME/.bashrc &&\
    echo "alias cdckan='cd /usr/lib/ckan/venv/src/ckan'" >> $HOME/.bashrc

COPY ckan $CKAN_VENV/src/ckan

WORKDIR $CKAN_VENV/src/ckan

# Setup CKAN
RUN ckan-pip install --upgrade pip &&\
    ckan-pip install wheel && \
    ckan-pip install --upgrade -r $CKAN_VENV/src/ckan/requirement-setuptools.txt && \
    ckan-pip install -r /usr/lib/ckan/venv/src/ckan/requirements.txt &&\
    ckan-pip install -r /usr/lib/ckan/venv/src/ckan/dev-requirements.txt &&\
    ckan-pip install ckanapi
RUN ckan-pip install -e $CKAN_VENV/src/ckan/ && \
    chown -R ckan:ckan $CKAN_HOME $CKAN_VENV $CKAN_CONFIG $CKAN_STORAGE_PATH
USER root

# Install all extensions with a remote source
RUN ckan-pip install -e "git+https://github.com/ckan/ckanext-spatial.git@f00ad5b1d981691ffa51fbd3bbef701d569943cb#egg=ckanext-spatial" && \
    ckan-pip install -r /usr/lib/ckan/venv/src/ckanext-spatial/requirements.txt
RUN ckan-pip install -e "git+https://github.com/EnviDat/ckanext-composite.git@1e6d7bb8fbe7d607376505860985c29816e64d36#egg=ckanext-composite"
RUN ckan-pip install -e "git+https://github.com/open-data/ckanext-repeating.git@291295557ff74b26784f6271c1a1b4ffdb990f43#egg=ckanext-repeating"
RUN ckan-pip install -e "git+https://github.com/ckan/ckanext-pages.git@v0.3.4#egg=ckanext-pages"
RUN ckan-pip install -e "git+https://github.com/datopian/ckanext-authz-service@bd4c80f55a714c1117a0e130d07463e383c494c7#egg=ckanext-authz-service" && \
    ckan-pip install -r "https://raw.githubusercontent.com/datopian/ckanext-authz-service/bd4c80f55a714c1117a0e130d07463e383c494c7/requirements.py3.txt"
# authz-service reqs overwrite: https://github.com/datopian/ckanext-authz-service/issues/27#issuecomment-913563305
RUN ckan-pip install "PyJWT[crypto]==2.1.0"
RUN ckan-pip install -e "git+https://github.com/ckan/ckanext-pdfview.git@3acd4a5d4cf53ca46bd3681e13e5d3ada051c644#egg=ckanext-pdfview"
RUN ckan-pip install -e "git+https://github.com/ckan/ckanext-geoview.git@cc30270e84c50df17a7a9f00b1223219dc3afa52#egg=ckanext-geoview"

RUN ckan-pip install -e "git+https://github.com/okfn/ckanext-sentry@d3b1d1cf1f975b3672891012e6c75e176497db8f#egg=ckanext-sentry"

# Install requirements for extensions with a local source
COPY ./ckanext-scheming/requirements.txt /usr/lib/ckan/scheming-requirements.txt
COPY ./ckanext-scheming/test-requirements.txt /usr/lib/ckan/test-scheming-requirements.txt
RUN ckan-pip install -r /usr/lib/ckan/scheming-requirements.txt -r /usr/lib/ckan/test-scheming-requirements.txt

COPY ./ckanext-validation/requirements.py3.txt /usr/lib/ckan/validation-requirements.txt
RUN ckan-pip install -r /usr/lib/ckan/validation-requirements.txt

COPY ./ckanext-harvest/pip-requirements.txt /usr/lib/ckan/harvest-requirements.txt
COPY ./ckanext-harvest/dev-requirements.txt /usr/lib/ckan/harvest-dev-requirements.txt
RUN ckan-pip install -r /usr/lib/ckan/harvest-dev-requirements.txt -r /usr/lib/ckan/harvest-requirements.txt

COPY ./ckanext-dhis2harvester/requirements.py3.txt /usr/lib/ckan/dhis2-harvester-requriments.txt
COPY ./ckanext-dhis2harvester/dev-requirements.txt /usr/lib/ckan/dhis2-harvester-dev-requriments.txt
RUN ckan-pip install -r /usr/lib/ckan/dhis2-harvester-requriments.txt -r /usr/lib/ckan/dhis2-harvester-dev-requriments.txt

COPY ./ckanext-restricted/requirements.txt /usr/lib/ckan/restricted-requirements.txt
RUN ckan-pip install -r /usr/lib/ckan/restricted-requirements.txt

COPY ./ckanext-unaids/requirements.txt /usr/lib/ckan/unaids-requirements.txt
COPY ./ckanext-unaids/dev-requirements.txt /usr/lib/ckan/unaids-dev-requirements.txt
RUN ckan-pip install -r /usr/lib/ckan/unaids-requirements.txt -r /usr/lib/ckan/unaids-dev-requirements.txt

COPY ./ckanext-blob-storage/requirements.py3.txt /usr/lib/ckan/blob-storage-requirements.txt
RUN ckan-pip install -r /usr/lib/ckan/blob-storage-requirements.txt

COPY ./ckanext-versions/requirements.txt /usr/lib/ckan/versions-requirements.txt
RUN ckan-pip install -r /usr/lib/ckan/versions-requirements.txt

COPY ./ckanext-auth/requirements.txt /usr/lib/ckan/auth-requirements.txt
RUN ckan-pip install -r /usr/lib/ckan/auth-requirements.txt

# CKAN 2.9.5 uses an older version of pytest-rerunfailures that doesn't work with newer PyTest
RUN ckan-pip install "pytest-rerunfailures==10.2"


RUN rm /usr/lib/ckan/*-requirements.txt

RUN apt-get -q -y update && apt-get -q -y install curl
RUN curl -sL https://deb.nodesource.com/setup_16.x | bash - && apt-get install nodejs && npm version
RUN npm install --global yarn

# Configs
COPY ./adx_develop/ckan/ckan-entrypoint-adx.sh /ckan-entrypoint.sh
COPY ./adx_develop/ckan/wait-for-it.sh /wait-for-it.sh
ENTRYPOINT ["/ckan-entrypoint.sh"]
