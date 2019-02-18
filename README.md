# ckan_infrastructure

Repository to run Fjelltopp version of CKAN

1. Clone repos:
     ```
     git clone https://github.com/ckan/ckan
     git clone https://github.com/fjelltopp/ckanext-superset
     git clone https://github.com/fjelltopp/ckanext-ukraine
     git clone https://github.com/fjelltopp/ckan_infrastructure
     git clone https://github.com/fjelltopp/ckanext-unaids
     ```
2. Then add: `127.0.0.1 ckan` to your `/etc/hosts` file
3. Start the stack:
     ```
     docker-compose -f docker-compose.yml -f dev.yml up -d
     ```
     If you want to start the UNAIDS version use unaids.yml instead of dev.yml in the above commands


4. After the images have been bulit and started run the following command to set up DB for datastore:
    ```
    docker exec ckan /usr/local/bin/ckan-paster --plugin=ckan datastore set-permissions -c /etc/ckan/production.ini | docker exec -i db psql -U ckan
    ```

5. Create an admin user:
    ```
    docker exec -it ckan /usr/local/bin/ckan-paster --plugin=ckan sysadmin -c /etc/ckan/production.ini add admin
    ```

6. Then restart the ckan container:
     ```
     docker-compose -f docker-compose.yml -f dev.yml restart ckan
     ```
7. CKAN should be available at http://localhost:5000
