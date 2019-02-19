#!/bin/bash
# ==============================================================================
#
# THIS FILE HOLDS THE DEFINITIVE LIST OF CKAN EXTENSIONS. To add an extension:
#
# - Decide whether it will require local development or not.
# - If local development required:
#   * Clone the code to your base ADX folder.
#   * Add the path of the requirements.txt file to the local_extensions list.
#   * Configure the adx_config.ini according to ckan documentation
# - If a remote extension:
#   * Get the pip install url
#   * Add this url to the list of remote extensions
#   * Configure the adx_config.ini according to the ckan documentation
# - Finally rebuild the docker image.
#
# ==============================================================================

set -e

# A list of all the local extensions to install into CKAN
# By default looks for e.g. ckanext-cloudstorage/requirements.txt
local_extensions=(
  "ckanext-unaids"
  "ckanext-cloudstorage"
)

# A list of pip urls for remote extensions to install e.g. from github
remote_extensions=(
  "git+https://github.com/ckan/ckanext-spatial.git#egg=ckanext-spatial"
  "git+https://github.com/ckan/ckanext-geoview.git#egg=ckanext-geoview"
)

# Two possible arguments: BUILD & RUN
if [ "$1" == "BUILD" ]; then
  # Install CKAN dev requirements
  ckan-pip install -r /usr/lib/ckan/venv/src/ckan/dev-requirements.txt

  # Do a simple pip install of the remote extensions
  for i in "${remote_extensions[@]}"
  do
    ckan-pip install $i
  done

  # Local extensions need to be updatable easily. You therefore need to do two
  # steps: firstly install requirements manually, then add the module path to the
  # PYTHONPATH. This way code changes are automatically picked up.
  for i in "${local_extensions[@]}"
  do
    FILENAME="/etc/adx/$i/requirements.txt"
    [[ -f $FILENAME ]] && ckan-pip install -r $FILENAME
  done
  exit 0

# SETTING PYTHON PATH
elif [ "$1" == "RUN" ]
then
  for i in "${local_extensions[@]}"
  do
    FILENAME="/etc/adx/$i/requirements.txt"
    [[ -f $FILENAME ]] && ckan-pip install -r $FILENAME
  done
  exit 0
fi
