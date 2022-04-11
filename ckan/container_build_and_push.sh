#!/bin/sh
docker build -t fjelltopp/ckan:development_base -f ckan/Dockerfile ./ckan/ && \
docker push fjelltopp/ckan:development_base
