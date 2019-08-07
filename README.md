# adx_develop

Repository storing the development environment for _The AIDS Data Repository_.

## Linked Repositories

Setting up the ADX development environment locally will clone a collection of different Github repos specified in [this file](https://github.com/fjelltopp/adx_manifest/blob/master/default.xml).  This includes the base [CKAN](https://github.com/ckan/ckan) repository and a variety of of forked CKAN extensions.


## Setup

1. Create a directory to store the ADX development environment, then change
   directory into it e.g.
   ```
   mkdir ~/fjelltopp/adx
   cd ~/fjelltopp/adx
   ```

2. Clone the `adx_develop` repo from Github into the directory
   ```
   git clone git@github.com:fjelltopp/adx_develop.git
   ```

3. Add a sym link to the dev env script from your $PATH:
   ```
   sudo ln -s `pwd`/adx_develop/adx /usr/local/bin/adx
   ```
   This shorthand sript can now be used from anywhere in your file system to
   issue a command to the adx development environment. Run `adx -h` for more
   information.

4. Setup the ADX code base.
   ```
   adx setup
   ```
   This command will clone all the other required git repos into your adx
   directory.  It will create local master branches for each repo and check
   the branch out. It uses a script by Google called "repo" to do this. Repo
   may require a name and an email.

5. Build and run the docker images as docker containers.
   ```
   adx up
   ```

6. You can view the start up logs of the ckan container using the command:
   ```
   adx logs ckan
   ```
   You should watch the logs and wait until all the ckan extensions have been properly installed before continuing. 

7. Do the initial CKAN configuration with:
    ```
    adx initCkanDb
    ```
    Which wraps the following steps for you:
    1. Setting up the db with the required tables for ckan and it's extensions:
       ```
       docker exec ckan /usr/local/bin/ckan-paster --plugin=ckan datastore set-permissions -c /etc/ckan/production.ini | docker exec -i db psql -U ckan
       docker exec ckan /usr/local/bin/ckan-paster --plugin=ckanext-ytp-request initdb -c /etc/ckan/production.ini
       docker exec -it ckan /usr/local/bin/ckan-paster --plugin=ckanext-harvest harvester initdb -c /etc/ckan/production.ini
       docker exec -it ckan /usr/local/bin/ckan-paster --plugin=ckanext-validation validation init-db -c /etc/ckan/production.ini
       ```

    2. Creating an admin user to access the site with:
       ```
       docker exec -it ckan /usr/local/bin/ckan-paster --plugin=ckan sysadmin -c /etc/ckan/production.ini add admin
       ```
    The db should persist in a docker volume, so these commands will only need to
    be run again if you delete corresponding docker volume.

8. Then restart the ckan container:
   ```
   adx restart ckan
   ```

9. CKAN should be available at http://localhost:5000

10. To use the Harvester extension in development run:
    ```
    adx bash ckan
    # run harvester fetch and gather consumer as bg tasks
    /adx_utils/harvester_bg_tasks.sh
    # then after each run of harvest job you need to run
    /adx_utils/harvester_run_task.sh
    ```

## Running CKAN tests locally

CKAN tests can be run in the development environment, but some setup is required.

To create and setup the test databases:
```
docker exec -it db createdb -O ckan ckan_test -E utf-8 -U postgres
docker exec -it db createdb -O ckan datastore_test -E utf-8 -U postgres
docker exec ckan /usr/local/bin/ckan-paster datastore set-permissions -c test-core.ini | docker exec -i db psql -U postgres
```

Tests should be run with the version of nosetests-2.7 installed in CKAN's virtual environment.  There is an alias set up inside the docker container called "ckan-nosetests" that points to this
executable. To run the ckan core tests:

```
docker exec -it ckan ckan-nosetests --ckan --with-pylons=/etc/ckan/test-core.ini ckan ckanext
```
