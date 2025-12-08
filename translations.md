# Translations

There are two options to support translating ADR:

1. Using adx_develop helpers to deal with all ADR extensions at once
2. Manually by interacting with a single extension

## For all extensions with adx_develop

adx_develop repo includes a utility script to help translate all extension repos quickly and easily. It should be used as follows:

1. Check that the list of extensions to be translated, and the list of languages they should be translated into, is complete in at the top of the translate.sh script.  The script should be located at: `adx_develop/translate.sh`.
2. Ensure you have latest development branch checked out everywhere. You can use `adx forall` to create translation branches in all neseccary repos quickly E.g. (if not using submodules): 

    ```shell
    adx forall ckanext-unaids ckanext-restricted ckanext-scheming ckanext-validation ckanext-ytp-request ckanext-emailasusername ckanext-pages ckanext-dhis2harvester ckanext-harvest ckanext-blob-storage ckanext-versions -c git checkout -b ADX-789-translations 
    ```

3. If using submodules, use: 

    ```shell
    git submodule foreach 'git checkout -b ADX-789-translations'
    ```

4. Update all the message catalogs and copy the resulting .po files into a single directory using the command:

    ```shell
    adx bash ckan
    /usr/lib/adx/adx_develop/translate.sh update_catalogs
    ```

5. If using submodules: 

    ```shell
    /usr/lib/adx/translate.sh update_catalogs
    ```

6. Select all the language folders in `/adx_develop/build/translations/` containing po files and zip them up to send to the translator.  You probably want to use `adx forall` (similar to step 2) at this point to commit and push the updated message catalogs to github.
7. Once you have the translated po files back from the translator, ensure you copy them back to the `/adx_develop/build/translations/` folder exactly as you found them at the end of step 3.
8. Run the following command to copy all files back to their original location.

    ```shell
    adx bash ckan
    /usr/lib/adx/adx_develop/translate.sh copy_translations
    ```

9. Check that the files have been properly copied across.

    ```shell
    adx status
    ```

10. Compile all translations with the following command:

    ```shell
    adx bash ckan
    /usr/lib/adx/adx_develop/translate.sh compile_catalogs
    ```

    Check no error messages appear in the logs.

11. Review the site in the local dev env to check formatting.

12. Use an `adx forall` command to commit and push all updated translations to github quickly.  You'll then need to manually open PRs for each repo.

## For a single extension

If you have a local working ADR venv you can skip steps 0, 1 (using python env from ckan container) and 5 (change file access).

In brief:

1. SSH into the ckan container

    ```shell
    adx bash ckan     source ../../bin/activate     cd /usr/lib/adx/ckanext-extension-name/
    ```

2. Generate the `.pot` file to extract the strings from your extension

    ```shell
    adx bash ckan
    cd /usr/lib/ckan/venv/
    source bin/activate
    cd /usr/lib/adx/submodules/ckanext-unaids
    ```

3. Generate the `.pot` file to extract the strings from your extension
    
    ```shell
    python setup.py extract_messages
    ```

4. If there is no `.po` already set up, init it:

    ```shell
    python setup.py init_catalog --locale fr
    python setup.py init_catalog --locale pt_PT
    ```

5. If there is a `.po`, update it:

    ```shell
    python setup.py update_catalog --locale fr
    python setup.py update_catalog --locale pt_PT
    ```

6. Give yourself edit-access to the `.po/.mo` files:

    ```shell
    chmod -R 777 /usr/lib/adx/submodules/ckanext-unaids/ckanext/unaids/i18n/
    ```

7. Make updates to the `.po` files
8. Compile the `.po` files into the `.mo` files

    ```shell
    python setup.py compile_catalog 
    ```

9. Restart the ckan container to see the changes

## CKAN Docs

- [Internationalizing strings in extensions — CKAN 2.9.11 documentation](https://docs.ckan.org/en/2.9/extensions/translating-extensions.html)
