$location = Get-Location

$resolved_path = Resolve-Path $location\..\..\ckan\requirement-setuptools.txt | select -ExpandProperty ProviderPath
pip install -r $resolved_path

pip install ckanapi

$resolved_path = Resolve-Path $location\..\..\ckan\requirements.txt | select -ExpandProperty ProviderPath
pip install -r $resolved_path

$resolved_path = Resolve-Path $location\..\..\ckan\dev-requirements.txt | select -ExpandProperty ProviderPath
pip install -r $resolved_path

pip install -e "git+https://github.com/ckan/ckanext-spatial.git@ce4f03bcd2000f98de1a9534dce92de674eb9806#egg=ckanext-spatial"
#pip install -r ${DIR}/../../ckanext-spatial/pip-requirements.txt
pip install -e "git+https://github.com/EnviDat/ckanext-composite.git@23a060b03d2432a58cc66968d93a15f5f1654055#egg=ckanext-composite"
pip install -e "git+https://github.com/open-data/ckanext-repeating.git@291295557ff74b26784f6271c1a1b4ffdb990f43#egg=ckanext-repeating"
pip install -e "git+https://github.com/okfn/ckanext-sentry@d3b1d1cf1f975b3672891012e6c75e176497db8f#egg=ckanext-sentry"

$resolved_path = Resolve-Path $location\..\..\ckanext-scheming\requirements.txt | select -ExpandProperty ProviderPath
pip install -r $resolved_path

$resolved_path = Resolve-Path $location\..\..\ckanext-scheming\test-requirements.txt | select -ExpandProperty ProviderPath
pip install -r $resolved_path

$resolved_path = Resolve-Path $location\..\..\ckanext-geoview\pip-requirements.txt | select -ExpandProperty ProviderPath
pip install -r $resolved_path

$resolved_path = Resolve-Path $location\..\..\ckanext-validation\requirements.txt | select -ExpandProperty ProviderPath
pip install -r $resolved_path

$resolved_path = Resolve-Path $location\..\..\ckanext-harvest\pip-requirements.txt | select -ExpandProperty ProviderPath
pip install -r $resolved_path

$resolved_path = Resolve-Path $location\..\..\ckanext-harvest\dev-requirements.txt | select -ExpandProperty ProviderPath
pip install -r $resolved_path

$resolved_path = Resolve-Path $location\..\..\ckanext-dhis2harvester\pip-requirements.txt | select -ExpandProperty ProviderPath
pip install -r $resolved_path

$resolved_path = Resolve-Path $location\..\..\ckanext-dhis2harvester\dev-requirements.txt | select -ExpandProperty ProviderPath
pip install -r $resolved_path

$resolved_path = Resolve-Path $location\..\..\ckanext-file_uploader_ui\requirements.txt | select -ExpandProperty ProviderPath
pip install -r $resolved_path

$resolved_path = Resolve-Path $location\..\..\ckanext-restricted\requirements.txt | select -ExpandProperty ProviderPath
pip install -r $resolved_path

pip install -r ${DIR}/../../ckanext-file_uploader_ui/requirements.txt
pip install -r ${DIR}/../../ckanext-restricted/requirements.txt
