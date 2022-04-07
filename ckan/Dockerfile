# See CKAN docs on installation from Docker Compose on usage
FROM ubuntu:focal
MAINTAINER Open Knowledge

# Set timezone
ENV TZ=UTC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Setting the locale
ENV LC_ALL=en_US.UTF-8
RUN apt-get update
RUN apt-get install --no-install-recommends -y locales
RUN sed -i "/$LC_ALL/s/^# //g" /etc/locale.gen
RUN dpkg-reconfigure --frontend=noninteractive locales
RUN update-locale LANG=${LC_ALL}

# Install required system packages
RUN apt-get -q -y update \
    && DEBIAN_FRONTEND=noninteractive apt-get -q -y upgrade \
    && apt-get -q -y install \
        python2.7\
        python2-dev \
        python-wheel-common \
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
        curl \
        xmlsec1 \
        jq \
        supervisor \
    && apt-get -q clean \
    && rm -rf /var/lib/apt/lists/*
RUN curl -sSL https://bootstrap.pypa.io/pip/2.7/get-pip.py --output get-pip.py
RUN python2 get-pip.py
RUN pip install pipenv==2021.5.29 uwsgi
RUN curl -sL https://deb.nodesource.com/setup_14.x | bash - && apt install nodejs -y && npm version
RUN npm install --global yarn
RUN mkdir -p /var/lib/ckan/resources && chmod 777 -R /var/lib/ckan


# Define environment variables
ENV CKAN_HOME /usr/lib/ckan
ENV CKAN_VENV $CKAN_HOME/venv
ENV CKAN_CONFIG /etc/ckan
ENV CKAN_STORAGE_PATH=/var/lib/ckan

# Build-time variables specified by docker-compose.yml / .env
ARG CKAN_SITE_URL

# Build-time variables specified by docker-compose.yml / .env
ENV PATH=${CKAN_VENV}/bin:${PATH}
COPY ckan-entrypoint-adx.sh /ckan-entrypoint.sh
COPY wait-for-it.sh /wait-for-it.sh
COPY bootstrap.sh /bootstrap.sh
# Add CKAN user
RUN useradd -r -u 900 -m -c "ckan account" -d $CKAN_HOME -s /bin/false ckan

RUN chmod +x /*.sh 

# Configs
USER root
EXPOSE 5000

ENTRYPOINT ["/ckan-entrypoint.sh"]
