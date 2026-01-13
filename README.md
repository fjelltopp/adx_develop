# adx_develop

Repository storing the development environment for The AIDS Data Repository.

## Linked Repositories

Setting up the ADX development environment locally will clone a collection of different Github repos set as submodules to the adx_develop repository. They’re located in adx_develop/submodules directory.

## Requirements

Python Docker Docker-compose

## Setup

1. Create a directory to store the ADX development environment, then change directory into it e.g.

   ```shell
   mkdir -p ~/fjelltopp/adx
   cd ~/fjelltopp/adx
   ```

2. Clone the `adx_develop` repo from Github into the directory

   ```shell
   git clone git@github.com:fjelltopp/adx_develop.git
   ```

3. Initialize git submodules

   ```shell
   git submodule update --init
   # or
   adx init
   ```

4. Add adr.local as localhost name to `/etc/hosts`. After the addition the file should look something like

   ```shell
   127.0.0.1       localhost
   127.0.0.1       adr.local
   ```

5. Add a symlink to the dev env script from your $PATH:

   ```shell
   sudo ln -s `pwd`/adx_develop/adx /usr/local/bin/adx
   ```

   This shorthand script can now be used from anywhere in your file system to issue a command to the adx development environment. Run `adx -h` for more information.

6. Environment variables configuration: Clone the template `dev.env` file to `.env` where you can tweak the configuration:

   ```shell
   cp adx_develop/dev.env adx_develop/.env
   ```

   Things you need to update manually are:

   - `ADX_PATH` to the path of the root directory containing adx_develop
   - `FJELLTOPP_PASSWORD=fjellt0pp-he@lth` for demo data loading scripts
   - `ADR_CKAN_SAML_IDP_CERT` to value from Fjelltopp development auth0 account [advanced settings](https://manage.auth0.com/dashboard/eu/hivtools/applications/lMiD8vQo1OZUPJEzd5hPvcxgTMkyY7YS/settings)

7. Setup the ADX code base.

   ```shell
   adx setup
   ```

   This command will initialize all git submodules, will reset all submodules to the development branch and will pull latest changes

8. Build and run the docker images as docker containers.

   ```shell
   adx up
   ```

9. You can view the start up logs of the ckan container using the command:

   ```shell
   adx logs ckan
   ```

   You should watch the logs and wait until all the ckan extensions have been properly installed before continuing.

10. Do the initial CKAN configuration with:

    ```shell
    adx dbsetup
    ```

    Which initializes the db tables for extensions and creates the admin user.

    Admin user:

    ```toml
    username: admin
    email: admin@fjelltopp.org
    password: fjellt0pp-he@lth
    ```

    The db should persist in a docker volume, so these commands will only need to be run again if you delete corresponding docker volume.

11. Then restart the ckan container:

    ```shell
    adx restart ckan
    ```

12. [Optional] Adding demo data to CKAN instance with:

    ```shell
    adx demodata
    ```

    Demo data accounts all have password: fjellt0pp-he@lth

13. CKAN should be available at [http://adr.local/](http://adr.local/)

## Docker images for feature branches

New feature which require changes to docker images can create problems when switching from feature-branch work back to development (to work on important bug fixes, reviewing PRs etc.)

In `.env` you can change the value of:

```env
IMAGE_TAG=development
CKAN_IMAGE_TAG=development
```

to a custom value representing your feature branch, e.g. 'versioning' to be able to quickly switch between different ADR versions. That way after switching to a different git branch you won't have to rebuild all of the images. `CKAN_IMAGE_TAG` is used to test custom CKAN containers if any changes have been made to `./ckan/` directory.

## Resetting the code base

The adx script comes with a convienience command forall that enables you to quickly replicate commands across multiple repos. The command can be used to reset your code base once everything you want to keep is committed and ideally pushed.

```shell
adx setup
# or the same using git command:
git submodule foreach "git reset --hard  || :"
git submodule foreach "git checkout development|| :"
git submodule foreach "git pull || :"
```

## Cleaning build artifacts

If you encounter issues with `pipenv lock` failing due to permission errors on `.egg-info` directories (especially after running containers as root), you can clean these build artifacts:

```shell
adx clean
```

This command will remove all `.egg-info` directories from the submodules, using `sudo` if necessary when files are owned by root.

## Using a fake SMTP server

We're using [rnwood/smtp4dev](https://github.com/rnwood/smtp4dev) to "fake" an SMTP service, it's deployed as part of docker compose - smtp container. It catches all the emails sent to it, accepts any credentials. Emails can be viewed via a web console available at port 5555, so if your local environment uses "adr.local" as a host name you can access at [http://adr.local:5555/](http://adr.local:5555/).

## Running CKAN tests locally

CKAN tests can be run in the development environment, but some setup is required.

To create and setup the test databases:

```shell
adx testsetup
```

Tests should be run with the version of nosetests-2.7 installed in CKAN's virtual environment. There is an alias set up inside the docker container called "ckan-nosetests" that points to this executable.

```shell
adx test extension_name
```

e.g.

```shell
adx test restricted
```

To run specific test case you can you -k pytest arg:

```shell
adx test restricted -k test_regression_example
```

To run the ckan core tests:

```shell
docker exec -it ckan ckan-nosetests --ckan --with-pylons=/usr/lib/ckan/venv/src/ckan/test-core.ini ckan ckanext
```

## Debugging with ipdb

You can debug the adx using the python debugger (pdb), or the improved interactive python debugger (ipdb). To do this set a break point as normal anywhere in the code:

```python
import ipdb; ipdb.set_trace()
```

Start the dev env in detached mode as normal:

```shell
adx up
```

Then attach to ckan container:

```shell
docker attach ckan
```

When your code hits the breakpoint it will open an interactive ipdb prompt. When you are finished you can detach from the container, without killing it, using the escape sequence: `ctrl-p` then `ctrl-q`.

See the [pdb docs](https://docs.python.org/3/library/pdb.html) and the [ipdb github](https://github.com/gotcha/ipdb) for more on how to debug with pdb/ipdb.

## Logs

To get more log output you can pick custom log level with -log, e.g.:

```shell
adx --log info demodata
```

## Translations

Please have a look at: [ADR Translations](./translations.md)

## Creating an extension

SSH into the container:

```shell
adx bash ckan
```

Create your extension:

```shell
cd /usr/lib/adx
ckan generate extension
```

Exit the docker container and run:

```shell
chmod -R 775 ckanext-hello_world
chown -R 1000:1000 ckanext-hello_world
```

Update the ckan config file:

- Open `adx_develop/ckan/adx_config.ini`
- Find `ckan.plugins` and add `hello_world` to the beginning of the list

Add the entrypoint:

- Open `adx_develop/ckan/ckan-entrypoint-adx.sh`
- Towards the bottom, add: `ckan-pip install --no-deps -e /usr/lib/adx/ckanext-hello_world`

Update the /adx_develop/ckan/Dockerfile with:

```shell
COPY ./ckanext-hello_world/requirements.txt /usr/lib/ckan/hello_world-requirements.txt
RUN ckan-pip install -r /usr/lib/ckan/hello_world-requirements.txt
```

Test ckan builds:

```shell
adx build ckan
adx up
adx logs ckan
```

Now let's make the extension do something

- Create an `index.html` file in `ckanext-hello_world/ckanext/hello_world/templates/home`
- Save `<h1>Hello World!</h1>` to it
- Run another `adx build ckan; adx up` and your browser should display Hello World!
- Read the [docs](https://docs.ckan.org/en/2.9/theming/templates.html#customizing-ckan-s-templates) for more info

## Setting up production deployments

Configure ADX_PATH env in your `.bashrc`, e.g.

```shell
export ADX_PATH=$HOME/fjelltopp/adr
```

Clone the following additional repos into your ADX_PATH:

```shell
git clone git@github.com:fjelltopp/adx_deploy.git
git clone git@github.com:fjelltopp/adx_manifest.git
```

Now you should be able to use the following command to draft PRs for prod deployment
Note: This only works with google chrome.

```shell
adx deploy
```
