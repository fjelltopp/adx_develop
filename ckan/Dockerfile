# See CKAN docs on installation from Docker Compose on usage
FROM debian:stretch
MAINTAINER Open Knowledge

# Install required system packages
RUN apt-get -q -y update \
    && DEBIAN_FRONTEND=noninteractive apt-get -q -y upgrade \
    && apt-get -q -y install \
        python-dev \
        python-pip \
        python-virtualenv \
        python-wheel \
        libpq-dev \
        libxml2-dev \
        libxslt-dev \
        libgeos-dev \
        libssl-dev \
        libffi-dev \
        postgresql-client \
        build-essential \
        git-core \
        vim \
        wget \
        jq \
        supervisor \
    && apt-get -q clean \
    && rm -rf /var/lib/apt/lists/*

# Define environment variables
ENV CKAN_HOME /usr/lib/ckan
ENV CKAN_VENV $CKAN_HOME/venv
ENV CKAN_CONFIG /etc/ckan
ENV CKAN_STORAGE_PATH=/var/lib/ckan
ENV CKAN_METASTORE $CKAN_STORAGE_PATH/metastore
# Build-time variables specified by docker-compose.yml / .env
ARG CKAN_SITE_URL

# Create ckan user
RUN useradd -r -u 900 -m -c "ckan account" -d $CKAN_HOME -s /bin/false ckan

# Setup virtual environment for CKAN
RUN mkdir -p $CKAN_VENV $CKAN_CONFIG $CKAN_STORAGE_PATH $CKAN_METASTORE && \
    virtualenv $CKAN_VENV && \
    ln -s $CKAN_VENV/bin/pip /usr/local/bin/ckan-pip &&\
    ln -s $CKAN_VENV/bin/ckan /usr/local/bin/ckan &&\
    ln -s $CKAN_VENV/bin/paster /usr/local/bin/ckan-paster &&\
    ln -s $CKAN_VENV/bin/python /usr/local/bin/ckan-python &&\
    ln -s $CKAN_VENV/bin/nosetests-2.7 /usr/local/bin/ckan-nosetests &&\
	ln -s $CKAN_VENV/bin/pytest /usr/local/bin/ckan-pytest &&\
    echo "alias cdckanext='cd /usr/lib/adx/'" >> $HOME/.bashrc &&\
    echo "alias cdckan='cd /usr/lib/ckan/venv/src/ckan'" >> $HOME/.bashrc

COPY ckan $CKAN_VENV/src/ckan

WORKDIR $CKAN_VENV/src/ckan

# Setup CKAN
RUN ckan-pip install --upgrade pip &&\
    ckan-pip install --upgrade -r $CKAN_VENV/src/ckan/requirement-setuptools.txt && \
    ckan-pip install -r /usr/lib/ckan/venv/src/ckan/requirements-py2.txt &&\
    ckan-pip install -r /usr/lib/ckan/venv/src/ckan/dev-requirements.txt &&\
    ckan-pip install ckanapi
RUN ckan-pip install -e $CKAN_VENV/src/ckan/ && \
    chown -R ckan:ckan $CKAN_HOME $CKAN_VENV $CKAN_CONFIG $CKAN_STORAGE_PATH $CKAN_METASTORE
USER root

# Install all extensions with a remote source
RUN ckan-pip install "git+https://github.com/ckan/ckanext-spatial.git@ce4f03bcd2000f98de1a9534dce92de674eb9806#egg=ckanext-spatial" && \
    ckan-pip install -r /usr/lib/ckan/venv/src/ckanext-spatial/pip-requirements.txt
RUN ckan-pip install "git+https://github.com/EnviDat/ckanext-composite.git@23a060b03d2432a58cc66968d93a15f5f1654055#egg=ckanext-composite"
RUN ckan-pip install "git+https://github.com/open-data/ckanext-repeating.git@291295557ff74b26784f6271c1a1b4ffdb990f43#egg=ckanext-repeating"
RUN ckan-pip install "git+https://github.com/okfn/ckanext-sentry@d3b1d1cf1f975b3672891012e6c75e176497db8f#egg=ckanext-sentry"
RUN ckan-pip install "git+https://github.com/datopian/ckanext-authz-service@v0.1.4#egg=ckanext-authz-service"
RUN ckan-pip install "git+https://github.com/datopian/ckanext-blob-storage@v0.6.0#egg=ckanext-external-storage"
RUN ckan-pip install -r /usr/lib/ckan/venv/src/ckanext-external-storage/requirements.py2.txt

# Install requirements for extensions with a local source
COPY ./ckanext-scheming/requirements.txt /usr/lib/ckan/scheming-requirements.txt
COPY ./ckanext-scheming/test-requirements.txt /usr/lib/ckan/test-scheming-requirements.txt
RUN ckan-pip install -r /usr/lib/ckan/scheming-requirements.txt -r /usr/lib/ckan/test-scheming-requirements.txt

COPY ./ckanext-geoview/pip-requirements.txt /usr/lib/ckan/geoview-requirements.txt
RUN ckan-pip install -r /usr/lib/ckan/geoview-requirements.txt

COPY ./ckanext-validation/requirements.txt /usr/lib/ckan/validation-requirements.txt
RUN ckan-pip install -r /usr/lib/ckan/validation-requirements.txt

COPY ./ckanext-harvest/pip-requirements.txt /usr/lib/ckan/harvest-requirements.txt
COPY ./ckanext-harvest/dev-requirements.txt /usr/lib/ckan/harvest-dev-requirements.txt
RUN ckan-pip install -r /usr/lib/ckan/harvest-dev-requirements.txt -r /usr/lib/ckan/harvest-requirements.txt

COPY ./ckanext-dhis2harvester/pip-requirements.txt /usr/lib/ckan/dhis2-harvester-requriments.txt
COPY ./ckanext-dhis2harvester/dev-requirements.txt /usr/lib/ckan/dhis2-harvester-dev-requriments.txt
RUN ckan-pip install -r /usr/lib/ckan/dhis2-harvester-requriments.txt -r /usr/lib/ckan/dhis2-harvester-dev-requriments.txt

COPY ./ckanext-harvest/pip-requirements.txt /usr/lib/ckan/harvest-requriments.txt
RUN ckan-pip install -r /usr/lib/ckan/harvest-requriments.txt

COPY ./ckanext-file_uploader_ui/requirements.txt /usr/lib/ckan/file_uploader_ui-requirements.txt
RUN ckan-pip install -r /usr/lib/ckan/file_uploader_ui-requirements.txt

COPY ./ckanext-restricted/requirements.txt /usr/lib/ckan/restricted-requirements.txt
RUN ckan-pip install -r /usr/lib/ckan/restricted-requirements.txt

COPY ./ckanext-versions/requirements.txt /usr/lib/ckan/versions-requirements.txt
RUN ckan-pip install -r /usr/lib/ckan/versions-requirements.txt

RUN rm /usr/lib/ckan/*-requirements.txt

RUN  apt-get -q -y update && apt-get -q -y install curl
RUN curl -sL https://deb.nodesource.com/setup_14.x | bash - && apt-get install nodejs && npm version
RUN npm install --global yarn

# Configs
COPY ./adx_develop/ckan/ckan-entrypoint-adx.sh /ckan-entrypoint.sh
COPY ./adx_develop/ckan/wait-for-it.sh /wait-for-it.sh
ENTRYPOINT ["/ckan-entrypoint.sh"]
