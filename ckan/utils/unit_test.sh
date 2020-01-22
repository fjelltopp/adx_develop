#!/usr/bin/env bash

module=$1

/usr/local/bin/ckan-nosetests --ckan --with-pylons=/usr/lib/adx/ckanext-${module}/test.ini /usr/lib/adx/ckanext-${module}/ckanext/${module}/tests --logging-level=WARNING
