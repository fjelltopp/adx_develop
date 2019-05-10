#!/usr/bin/env bash
ckan-paster --plugin=ckanext-harvest harvester fetch_consumer -c /etc/ckan/production.ini &
ckan-paster --plugin=ckanext-harvest harvester gather_consumer -c /etc/ckan/production.ini &
