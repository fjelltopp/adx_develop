#!/usr/bin/env bash
set -e

DIR="${BASH_SOURCE%/*}"
if [[ ! -d "$DIR" ]]; then DIR="$PWD"; fi

pip install -r ${DIR}/../../ckan/requirement-setuptools.txt
pip install ckanapi
pip install -r ${DIR}/../../ckan/requirements-py2.txt
pip install -r ${DIR}/../../ckan/dev-requirements.txt
pip install -e "git+https://github.com/ckan/ckanext-spatial.git@ce4f03bcd2000f98de1a9534dce92de674eb9806#egg=ckanext-spatial"
#pip install -r ${DIR}/../../ckanext-spatial/pip-requirements.txt
pip install -e "git+https://github.com/EnviDat/ckanext-composite.git@23a060b03d2432a58cc66968d93a15f5f1654055#egg=ckanext-composite"
pip install -e "git+https://github.com/open-data/ckanext-repeating.git@291295557ff74b26784f6271c1a1b4ffdb990f43#egg=ckanext-repeating"
pip install -e "git+https://github.com/okfn/ckanext-sentry@d3b1d1cf1f975b3672891012e6c75e176497db8f#egg=ckanext-sentry"
pip install -r ${DIR}/../../ckanext-scheming/requirements.txt
pip install -r ${DIR}/../../ckanext-scheming/test-requirements.txt
pip install -r ${DIR}/../../ckanext-geoview/pip-requirements.txt
pip install -r ${DIR}/../../ckanext-validation/requirements.txt
pip install -r ${DIR}/../../ckanext-harvest/pip-requirements.txt
pip install -r ${DIR}/../../ckanext-harvest/dev-requirements.txt
pip install -r ${DIR}/../../ckanext-dhis2harvester/pip-requirements.txt
pip install -r ${DIR}/../../ckanext-dhis2harvester/dev-requirements.txt
pip install -r ${DIR}/../../ckanext-harvest/pip-requirements.txt
pip install -r ${DIR}/../../ckanext-restricted/requirements.txt
pip install -r ${DIR}/../../ckanext-versions/requirements.txt
pip install -r ${DIR}/../../ckanext-googleanalytics/requirements.txt
