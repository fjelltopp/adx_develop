# adx_develop

Repository to the development environment for the AIDS data exchange.

1. Clone repos into a single parent directory:
     ```
     git clone https://github.com/fjelltopp/adx_develop
     git clone https://github.com/ckan/ckan
     git clone https://github.com/fjelltopp/ckanext-ukraine
     git clone https://github.com/fjelltopp/ckanext-unaids
     ```

2. Then add: `127.0.0.1 ckan` to your `/etc/hosts` file

3. Add a sym link the dev env script from your $PATH:
   ```
   cd adx_develop
   sudo ln -s `pwd`/adx /usr/local/bin/adx
   ```
   This shorthand sript can now be used from anywhere in your file system to issue a docker-compose command to the adx development environment.

3. Start the stack:
     ```
     adx up
     ```

4. After the images have been built and started run the following command to set up DB for datastore:
    ```
    docker exec ckan /usr/local/bin/ckan-paster --plugin=ckan datastore set-permissions -c /etc/ckan/production.ini | docker exec -i db psql -U ckan
    ```

5. Create an admin user:
    ```
    docker exec -it ckan /usr/local/bin/ckan-paster --plugin=ckan sysadmin -c /etc/ckan/production.ini add admin
    ```

6. Then restart the ckan container:
     ```
     adx restart ckan
     ```

7. CKAN should be available at http://localhost:5000
