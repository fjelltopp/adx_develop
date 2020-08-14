import json
import logging
import os

import ckanapi

DEMO_DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../demo_data/')
DEMO_USERS = os.path.join(DEMO_DATA_PATH, 'users.json')
DEMO_ORGANIZATIONS = os.path.join(DEMO_DATA_PATH, 'organizations.json')
# TODO: DEMO_DATASETS = os.path.join(DEMO_DATA_PATH, 'datasets.json')
# TODO: DEMO_HARVESTERS = os.path.join(DEMO_DATA_PATH, 'harvesters.json')

log = logging.getLogger(__name__)


def load_organizations(ckan):
    with open(DEMO_ORGANIZATIONS, 'r') as organizations_file:
        organizations = json.load(organizations_file)['organizations']
        for organization in organizations:
            try:
                ckan.action.organization_create(**organization)
                log.info(f"Created organization {organization['name']}")
                continue
            except ckanapi.errors.ValidationError as e:
                pass # fallback to organization update
            try:
                log.warning(f"Organization {organization['name']} might already exists. Will try to update.")
                id = ckan.action.organization_show(id=organization['name'])['id']
                ckan.action.organization_update(id=id, **organization)
                log.info(f"Updated organization {organization['name']}")
            except ckanapi.errors.ValidationError as e:
                log.error(f"Can't create organization {organization['name']}: {e.error_dict}")


def load_users(ckan):
    with open(DEMO_USERS, 'r') as users_file:
        users = json.load(users_file)['users']
        for user in users:
            try:
                ckan.action.user_create(**user)
                log.info(f"Created user {user['name']}")
                continue
            except ckanapi.errors.ValidationError as e:
                pass  # fallback to user update
            try:
                log.warning(f"User {user['name']} might already exists. Will try to update.")
                id = ckan.action.user_show(id=user['name'])['id']
                ckan.action.user_update(id=id, **user)
                log.info(f"Updated user {user['name']}")
            except ckanapi.errors.ValidationError as e:
                log.error(f"Can't create user {user['name']}: {e.error_dict}")


def load_data(adr_url, apikey):
    ckan = ckanapi.RemoteCKAN(adr_url, apikey=apikey)

    load_users(ckan)
    load_organizations(ckan)


if __name__ == '__main__':
    load_data('http://ckan:5000', "6011357f-a7f8-4367-a47d-8c2ab8059520")
