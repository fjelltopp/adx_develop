FROM ckan/ckan-solr:2.9-solr8
MAINTAINER CKAN

# Enviroment
ENV SOLR_CORE ckan

# Adding Files
ADD $BUILD_CONTEXT/solr/schema.xml /opt/solr/server/solr/configsets/ckan/conf/managed-schema

