#!/usr/bin/env bash
ckan-paster --plugin=ckanext-harvest harvester -c /etc/ckan/ckan.ini fetch_consumer &
ckan-paster --plugin=ckanext-harvest harvester -c /etc/ckan/ckan.ini gather_consumer &
