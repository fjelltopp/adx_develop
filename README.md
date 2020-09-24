# adx_develop

Repository storing the development environment for _The AIDS Data Repository_.

## Linked Repositories

Setting up the ADX development environment locally will clone a collection of different Github repos specified in [this file](https://github.com/fjelltopp/adx_manifest/blob/master/default.xml).  This includes the base [CKAN](https://github.com/ckan/ckan) repository and a variety of of forked CKAN extensions.


## Requirements
Python
Docker
Docker-compose

## Setup

1. Create a directory to store the ADX development environment, then change
   directory into it e.g.
   ```
   mkdir -p ~/fjelltopp/adx
   cd ~/fjelltopp/adx
   ```

2. Clone the `adx_develop` repo from Github into the directory
   ```
   git clone git@github.com:fjelltopp/adx_develop.git
   ```
   
2. Install `ckan_api` requirements using the `requirements.txt` file
   ```
   pip install -r ./adx_develop/requirements.txt
   ```
   
2. Add ckan as localhost name to `/etc/hosts`. After the addition the file should look something like
   ```
   127.0.0.1       localhost
   127.0.1.1       somehostname
   127.0.0.1       ckan
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
    adx dbsetup
    ```
    Which initializes the db tables for extensions and creates the admin user.
    
    **Admin user:**
    ```
    username: admin
    password: fjelltopp
   ```
    The db should persist in a docker volume, so these commands will only need to
    be run again if you delete corresponding docker volume.

8. Then restart the ckan container:
   ```
   adx restart ckan
   ```
   
9. [Optional] Adding demo data to CKAN instance with:
    ```
   adx demodata
   ```

9. CKAN should be available at http://localhost:5000


## Running CKAN tests locally

CKAN tests can be run in the development environment, but some setup is required.

To create and setup the test databases:
```
   adx testsetup
```

Tests should be run with the version of nosetests-2.7 installed in CKAN's virtual environment.  There is an alias set up inside the docker container called "ckan-nosetests" that points to this
executable.

```
adx test extension_name
```
e.g.
```
adx test restricted
```

To run the ckan core tests:
```
docker exec -it ckan ckan-nosetests --ckan --with-pylons=/usr/lib/ckan/venv/src/ckan/test-core.ini ckan ckanext
```

### Logs
To get more log output you can pick custom log level with `-log`, e.g.:
```
adx --log info demodata
```
