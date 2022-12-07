#!/bin/bash
#
# This script includes three tools to help with bulk translation operations:
# - One tool updates all translation .po files for every extension in the ADR project and copies
#   the resulting files into a single folder `./build/translations` for sharing with UNAIDS
# - A further tool then copies files from this folder back to their original location
# - A final tool then runs compile_catalog for every language and every extension
#
# It is recommended prior to running these commands that you ensure that you have every repo 
# checked out with latest development branch.  You may then use `adx forall` command to make bulk
# operations across all desired repos. 
#
# Also, check that the variables LANGUAGES and EXTENSIONS are set correctly prior to execution.
#
# To use this script: 
#    ```
#    adx bash ckan
#
#    bash /usr/lib/adx/translate.sh update_catalogs
#
#    # Translate files that have been copied to `build/translations`
#
#    bash /usr/lib/adx/translate.sh copy_translations
#
#    # Check that files have been correctly copied back to their original position
#
#    bash /usr/lib/adx/translate.sh compile_translations
#    ```

set -e # exit when any command fails

LANGUAGES=(
    fr
    pt_PT
)

EXTENSIONS=(
    unaids
    restricted
    scheming
    validation
    ytp-request
    emailasusername
    pages
    dhis2harvester
    harvest
    blob-storage
    versions
    # Untranslated extensions
    # geoview
)

read_manifest_xml () {
    local IFS=\/\>
    read -d \< ENTITY CONTENT
    local ret=$?
    TAG_NAME=${ENTITY%% *}
    ATTRIBUTES=${ENTITY#* }
    return $ret
}

process_extension () {
    if [[ $name == ckanext-* ]]; then
        name=ckanext-$extension
        echo $name
        cd /usr/lib/adx/$name
        python setup.py extract_messages

        for lang in ${LANGUAGES[*]}
        do
            if ! ls /usr/lib/adx/$name/ckanext/**/i18n/$lang 1> /dev/null 2>&1; then
                python setup.py init_catalog --locale $lang
            fi
            python setup.py update_catalog --locale $lang
            cp /usr/lib/adx/submodules/$name/ckanext/**/i18n/$lang/LC_MESSAGES/*.po /usr/lib/adx/build/translations/$lang/
        done
    fi
}

process_all_extensions () {
    for extension in ${EXTENSIONS[*]}
    do
        process_extension
    done
    cd /usr/lib/adx/build/translations
}

create_directory_structure () {
    for lang in ${LANGUAGES[*]}
    do
        mkdir -p /usr/lib/adx/build/translations/$lang/
    done
    rm -f /usr/lib/adx/build/translations/**/*.po
}

report_work_done () {
    echo "Extracted translation POs for..."
    printf "ckanext-%s " "${EXTENSIONS[@]}"
    echo ""
    echo "and language codes..."
    printf "%s " "${LANGUAGES[@]}"
    echo ""
}

copy_translations () {
    for extension in ${EXTENSIONS[*]}
    do
        for lang in ${LANGUAGES[*]}
        do
            folder_name=${extension//[-]/_}
            name=ckanext-$extension 
            cp /usr/lib/adx/build/translations/$lang/$name.po /usr/lib/adx/$name/ckanext/$folder_name/i18n/$lang/LC_MESSAGES/
        done
    done
}

compile_catalogs () {
    for extension in ${EXTENSIONS[*]}
    do
        name=ckanext-$extension
        echo $name
        cd /usr/lib/adx/$name
        for lang in ${LANGUAGES[*]}
        do
            python setup.py compile_catalog --locale $lang 
        done
    done
    cd /usr/lib/adx/build/translations
}

update_catalogs () {
    create_directory_structure
    process_all_extensions
    report_work_done
}

source /usr/lib/ckan/venv/bin/activate
$1 
deactivate
