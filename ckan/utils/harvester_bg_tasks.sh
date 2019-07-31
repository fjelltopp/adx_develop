#!/usr/bin/env bash
ckan-paster --plugin=ckanext-harvest harvester -c /etc/ckan/production.ini fetch_consumer &
ckan-paster --plugin=ckanext-harvest harvester -c /etc/ckan/production.ini gather_consumer &
