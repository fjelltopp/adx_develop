# adx_develop

Repository to the development environment for the AIDS data exchange.

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

5. Then add: `127.0.0.1 ckan` to your `/etc/hosts` file

6. Build and run the docker images as docker containers.
   ```
   adx up
   ```

7. After the images have been built and started run the following commands to set
   up DB for data-store:
   ```
   docker exec ckan /usr/local/bin/ckan-paster --plugin=ckan datastore set-permissions -c /etc/ckan/production.ini | docker exec -i db psql -U ckan
   docker exec ckan /usr/local/bin/ckan-paster --plugin=ckanext-ytp-request initdb -c /etc/ckan/production.ini
   ```
   For the request-access (ytp-requests) extension:
   ```
   docker exec ckan /usr/local/bin/ckan-paster --plugin=ckanext-ytp-request initdb -c /etc/ckan/production.ini
   ```
   For harvest ext:
   ```
   docker exec -it ckan /usr/local/bin/ckan-paster --plugin=ckanext-harvest harvester initdb -c /etc/ckan/production.ini
   ```

8. Create an admin user:
   ```
   docker exec -it ckan /usr/local/bin/ckan-paster --plugin=ckan sysadmin -c /etc/ckan/production.ini add admin
   ```
   The db should persist in a docker volume, so these commands will only need to
   be run again if you delete corresponding docker volume.

9. Then restart the ckan container:
   ```
   adx restart ckan
   ```

10. CKAN should be available at http://localhost:5000
