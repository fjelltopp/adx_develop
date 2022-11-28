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
   pip3 install --user -r ./adx_develop/requirements.txt
   ```

2. Add adr.local as localhost name to `/etc/hosts`. After the addition the file should look something like
   ```
   127.0.0.1       localhost
   127.0.0.1       adr.local
   ```

3. Add a sym link to the dev env script from your $PATH:
   ```
   sudo ln -s `pwd`/adx_develop/adx /usr/local/bin/adx
   ```
   This shorthand sript can now be used from anywhere in your file system to
   issue a command to the adx development environment. Run `adx -h` for more
   information.
   
3. Environment variables configuration:
   Clone the template `dev.env` file to `.env` where you can tweak the configuration:
   ```
   cp adx_develop/dev.env adx_develop/.env
   ```
   
4. Setup the ADX code base.
   ```
   adx setup
   ```
   This command will clone all the other required git repos into your adx
   directory.  It will create local master branches for each repo and check
   the branch out. It uses a script by Google called "repo" to do this. Repo
   may require a name and an email.

5. Ensure you have a Fjelltopp AWS account created for you and follow the [AWS SSO CLI docs here](https://fjelltopp.atlassian.net/wiki/spaces/NAV/pages/166494232/AWS+EKS+setup) on configuring your AWS CLI
6. 
   Now run
   ```
   AWS_PROFILE=fjelltopp-adr aws ecr get-login-password --region eu-west-1 | docker login --username AWS --password-stdin 254010146609.dkr.ecr.eu-west-1.amazonaws.com
   ```

6. Build and run the docker images as docker containers.
   ```
   adx up
   ```

7. You can view the start up logs of the ckan container using the command:
   ```
   adx logs ckan
   ```
   You should watch the logs and wait until all the ckan extensions have been properly installed before continuing.

8. Do the initial CKAN configuration with:
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

9. Then restart the ckan container:
   ```
   adx restart ckan
   ```

10. [Optional] Adding demo data to CKAN instance with:
    ```
    adx demodata
    ```

11. CKAN should be available at http://adr.local/


### [OPTIONAL] Setting up local ckan dev venv

1. For Ubuntu you'll need to satisfy psycopg2:
```
sudo apt-get install libpq-dev
```
2. Then install python2 and pip2 locally.
3. Activate your adr venv
4. Then you can run
```
adx_develop/util/install_requirements.sh
```

## Docker images for feature branches

New feature which require changes to docker images can create problems
when switching from feature-branch work back to development (to work
on important bug fixes, reviewing PRs etc.)

In `.env` you can change the value of:
```bash
IMAGE_TAG=development
```
to a custom value representing your feature branch, e.g. `'versioning'`
to be able to quickly switch between different ADR versions. That way
after switching to a different git branch you won't have to rebuild all
of the images.

## Resetting the code base

The adx script comes with a convienience command forall that enables you to quickly replicate commands across multiple repos.
The command can be used to reset your code base once everything you want to keep is committed and ideally pushed.

```
adx sync
adx forall -c git checkout development
adx forall -c git pull --rebase --preserve-merges
```

## Using a fake SMTP server

We're using https://github.com/rnwood/smtp4dev to "fake" an SMTP service, it's deployed as part of docker compose - smtp container. It catches all the emails sent to it, accepts any credentials. Emails can be viewed via a web console available at port 5555, so if your local environment uses "adr.local" as a host name you can access at http://adr.local:5555/

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
## Debugging with ipdb

You can debug the adx using the python debugger (pdb), or the improved interactive
python debugger (ipdb).  To do this set a break point as normal anywhere in
the code:
```
import ipdb; ipdb.set_trace()
```
Start the dev env in detached mode as normal:
```
adx up
```
Then attach to ckan container:
```
docker attach ckan
```
When your code hits the breakpoint it will open an interactive ipdb prompt.
When you are finished you can detach from the container, without killing it,
using the escape sequence: \[ctrl-p\]\[ctrl-q\].

See the [pdb docs](https://docs.python.org/3/library/pdb.html) and the [ipdb
github](https://github.com/gotcha/ipdb) for more on how to debug with pdb/ipdb.

## Configuring flak8 to run locally with PyCharm
```
How to manually setup flake8 as PyCharm external tool

File / Settings / Tools / External Tools / Add
Name: Flake8
Program: $PyInterpreterDirectory$/python
Parameters: -m flake8 --show-source --statistics --max-line-length=127 $FilePath$
Working directory: $ProjectFileDir$

Output Filters / Add
Name: Filter 1
Regular expression to match output:
$FILE_PATH$\:$LINE$\:$COLUMN$\:.*

Output Filters / Add
Name: Filter 2
Regular expression to match output:
$FILE_PATH$\:$LINE$\:.*

To check source with flake8:
Tools / External Tools / Flake8

Can be used with single files as well as with directories, recursively.
```

## Logs
To get more log output you can pick custom log level with `-log`, e.g.:
```
adx --log info demodata
```

## Translations

Please have a look at: https://fjelltopp.atlassian.net/wiki/spaces/ADR/pages/168591361/ADR+Translations


# Creating an extension

SSH into the container:
```
adx bash ckan
```

Create your extension:
```
cd /usr/lib/adx
ckan generate extension
```

Exit the docker container and run:
```
chmod -R 775 ckanext-hello_world
chown -R 1000:1000 ckanext-hello_world
```

Update the ckan config file:
- Open `adx_develop/ckan/adx_config.ini`
- Find `ckan.plugins` and add `hello_world` to the beginning of the list

Add the entrypoint:
- Open `adx_develop/ckan/ckan-entrypoint-adx.sh`
- Towards the bottom, add: `ckan-pip install --no-deps -e /usr/lib/adx/ckanext-hello_world`

Update the `/adx_develop/ckan/Dockerfile` with:
```
COPY ./ckanext-hello_world/requirements.txt /usr/lib/ckan/hello_world-requirements.txt
RUN ckan-pip install -r /usr/lib/ckan/hello_world-requirements.txt
```

Test ckan builds:
```
adx build ckan
adx up
adx logs ckan
```

Now let's make the extension do something
- Create an `index.html` file in `ckanext-hello_world/ckanext/hello_world/templates/home`
- Save `<h1>Hello World!</h1>` to it
- Run another `adx build ckan; adx up` and your browser should display `Hello World!`
- Read the [docs](https://docs.ckan.org/en/2.9/theming/templates.html#customizing-ckan-s-templates) for more info

# Setting up production deployments
1. Configure `ADX_PATH` env in your `.bashrc`, e.g.
    ```
    export ADX_PATH=$HOME/fjelltopp/adr
    ```
2. Clone the following additional repos into your `ADX_PATH`:
    ```
    git clone git@github.com:fjelltopp/adx_deploy.git
    git clone git@github.com:fjelltopp/adx_manifest.git
    ```
3. Now you should be able to use the following command to draft PRs for prod deployment

    Note: This only works with google chrome.
    ```
    adx deploy
    ```

