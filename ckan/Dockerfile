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

# Build-time variables specified by docker-compose.yml / .env
ARG CKAN_SITE_URL

# Create ckan user
RUN useradd -r -u 900 -m -c "ckan account" -d $CKAN_HOME -s /bin/false ckan

# Setup virtual environment for CKAN
RUN mkdir -p $CKAN_VENV $CKAN_CONFIG $CKAN_STORAGE_PATH && \
    virtualenv $CKAN_VENV && \
    ln -s $CKAN_VENV/bin/pip /usr/local/bin/ckan-pip &&\
    ln -s $CKAN_VENV/bin/paster /usr/local/bin/ckan-paster &&\
    ln -s $CKAN_VENV/bin/python /usr/local/bin/ckan-python &&\
    ln -s $CKAN_VENV/bin/nosetests-2.7 /usr/local/bin/ckan-nosetests &&\
    echo "alias ckanext='cd /usr/lib/adx/'" >> $HOME/.bashrc &&\
    echo "alias ckan='cd /usr/lib/ckan/venv/src/ckan'" >> $HOME/.bashrc

COPY ckan $CKAN_VENV/src/ckan

WORKDIR $CKAN_VENV/src/ckan

# Setup CKAN
RUN ckan-pip install -U pip && \
    ckan-pip install --upgrade -r $CKAN_VENV/src/ckan/requirement-setuptools.txt && \
    ckan-pip install --upgrade -r $CKAN_VENV/src/ckan/requirements.txt && \
    ckan-pip install -e $CKAN_VENV/src/ckan/ && \
    chown -R ckan:ckan $CKAN_HOME $CKAN_VENV $CKAN_CONFIG $CKAN_STORAGE_PATH
USER root

# Install dev requirements
RUN ckan-pip install -r /usr/lib/ckan/venv/src/ckan/dev-requirements.txt &&\
    ckan-pip install ckanapi

# Install all extensions with a remote source
RUN ckan-pip install -e "git+https://github.com/ckan/ckanext-spatial.git#egg=ckanext-spatial" && \
    ckan-pip install -r /usr/lib/ckan/venv/src/ckanext-spatial/pip-requirements.txt
RUN ckan-pip install -e "git+https://github.com/EnviDat/ckanext-composite.git#egg=ckanext-composite"
RUN ckan-pip install -e "git+https://github.com/open-data/ckanext-repeating.git#egg=ckanext-repeating"
RUN ckan-pip install -e "git+https://github.com/ckan/ckanext-harvest.git@v1.3.0#egg=ckanext-harvest" && \
    ckan-pip install -r /usr/lib/ckan/venv/src/ckanext-harvest/pip-requirements.txt
RUN ckan-pip install -e "git+https://github.com/okfn/ckanext-sentry#egg=ckanext-sentry"
RUN ckan-pip install -e "git+https://github.com/ckan/ckanext-pdfview#egg=ckanext-pdfview"
RUN ckan-pip install -e "git+https://github.com/fjelltopp/ckanext-googleanalytics.git#egg=ckanext-googleanalytics" && \
    ckan-pip install -r /usr/lib/ckan/venv/src/ckanext-googleanalytics/requirements.txt

# Install requirements for extensions with a local source
COPY ./ckanext-scheming/requirements.txt /usr/lib/ckan/scheming-requirements.txt
RUN ckan-pip install -r /usr/lib/ckan/scheming-requirements.txt

COPY ./ckanext-geoview/pip-requirements.txt /usr/lib/ckan/geoview-requirements.txt
RUN ckan-pip install -r /usr/lib/ckan/geoview-requirements.txt

COPY ./ckanext-issues/dev-requirements.txt /usr/lib/ckan/issues-requirements.txt
RUN ckan-pip install -r /usr/lib/ckan/issues-requirements.txt

COPY ./ckanext-validation/requirements.txt /usr/lib/ckan/validation-requirements.txt
RUN ckan-pip install -r /usr/lib/ckan/validation-requirements.txt

COPY ./ckanext-dhis2harvester/pip-requirements.txt /usr/lib/ckan/dhis2-harvester-requriments.txt
COPY ./ckanext-dhis2harvester/dev-requirements.txt /usr/lib/ckan/dhis2-harvester-dev-requriments.txt
RUN ckan-pip install -r /usr/lib/ckan/dhis2-harvester-requriments.txt -r /usr/lib/ckan/dhis2-harvester-dev-requriments.txt

COPY ./ckanext-file_uploader_ui/requirements.txt /usr/lib/ckan/file_uploader_ui-requirements.txt
RUN ckan-pip install -r /usr/lib/ckan/file_uploader_ui-requirements.txt

RUN rm /usr/lib/ckan/*-requirements.txt
# Configs
COPY ./adx_develop/ckan/ckan-entrypoint-adx.sh /ckan-entrypoint.sh
COPY ./adx_develop/ckan/wait-for-it.sh /wait-for-it.sh
ENTRYPOINT ["/ckan-entrypoint.sh"]
