import json
import logging
import os

import ckanapi

DEMO_DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../demo_data/')
DEMO_USERS = os.path.join(DEMO_DATA_PATH, 'users.json')
DEMO_ORGANIZATIONS = os.path.join(DEMO_DATA_PATH, 'organizations.json')
DEMO_HARVESTERS = os.path.join(DEMO_DATA_PATH, 'harvesters.json')
DEMO_DATASETS = os.path.join(DEMO_DATA_PATH, 'datasets.json')
DEMO_RESOURCES = os.path.join(DEMO_DATA_PATH, 'resources.json')

log = logging.getLogger(__name__)


def load_organizations(ckan):
    """
    Helper method to load demo organizations from DEMO_ORGANIZATIONS config json file
    :param ckan: ckanapi instance
    :return: a dictionary map of created organization names to their ids
    """
    organization_ids_dict = {}
    with open(DEMO_ORGANIZATIONS, 'r') as organizations_file:
        organizations = json.load(organizations_file)['organizations']
        for organization in organizations:
            org_name = organization['name']
            try:
                org = ckan.action.organization_create(**organization)
                log.info(f"Created organization {org_name}")
                organization_ids_dict[org_name] = org["id"]
                continue
            except ckanapi.errors.ValidationError as e:
                pass  # fallback to organization update
            try:
                log.warning(f"Organization {org_name} might already exists. Will try to update.")
                org_id = ckan.action.organization_show(id=org_name)['id']
                ckan.action.organization_update(id=org_id, **organization)
                organization_ids_dict[org_name] = org_id
                log.info(f"Updated organization {org_name}")
            except ckanapi.errors.ValidationError as e:
                log.error(f"Can't create organization {org_name}: {e.error_dict}")
    return organization_ids_dict


def load_users(ckan):
    """
    Helper method to load demo users from DEMO_USERS config json file
    :param ckan: ckanapi instance
    :return: None
    """
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


def load_harvesters(ckan, organizations_ids_dict):
    """
    Helper method to load demo users from DEMO_HARVESTERS config json file.
    field "owner_org" which is owner organization id is required by CKAN. Those ids are generated
    in this method by reading "owner_org_name" param from json input and with use of `organizations_ids_dict`
    translated to org_id and passed as `owner_org` field.
    :param ckan: ckanapi instance
    :param organizations_ids_dict: a dictionary map of created organization names to their ids
    """
    with open(DEMO_HARVESTERS, 'r') as harvesters_file:
        harvesters = json.load(harvesters_file)['harvesters']
        for harvester in harvesters:
            org_name = harvester.pop("owner_org_name")
            harvester["owner_org"] = organizations_ids_dict[org_name]
            try:
                ckan.action.package_create(**harvester)
                log.info(f"Created harvester {harvester['name']}")
                continue
            except ckanapi.errors.ValidationError as e:
                pass  # fallback to harvester update
            try:
                log.warning(f"Harvester {harvester['name']} might already exists. Will try to update.")
                id = ckan.action.package_show(id=harvester['name'])['id']
                ckan.action.package_update(id=id, **harvester)
                log.info(f"Updated harvester {harvester['name']}")
            except (ckanapi.errors.ValidationError, ckanapi.errors.NotFound) as e:
                log.error(f"Can't create harvester {harvester['name']}: {e!s}")


def load_datasets(ckan):
    """
    Helper method to load demo datasets from DEMO_DATASETS config json file
    :param ckan: ckanapi instance
    :return: None
    """
    with open(DEMO_DATASETS, 'r') as datasets_file:
        datasets = json.load(datasets_file)['datasets']
        for dataset in datasets:
            try:
                ckan.action.package_create(**dataset)
                log.info(f"Created dataset {dataset['name']}")
                continue
            except ckanapi.errors.ValidationError as e:
                pass  # fallback to dataset update
            try:
                log.warning(f"Dataset {dataset['name']} might already exists. Will try to update.")
                id = ckan.action.package_show(id=dataset['name'])['id']
                ckan.action.package_update(id=id, **dataset)
                log.info(f"Updated dataset {dataset['name']}")
            except ckanapi.errors.ValidationError as e:
                log.error(f"Can't create dataset {dataset['name']}: {e.error_dict}")


def load_resources(ckan):
    """
    Helper method to load demo resources
    :param ckan: ckanapi instance
    :return: None
    """
    with open(DEMO_RESOURCES, 'r') as resources_file:
        dataset_resources = json.load(resources_file)
    for dataset_id, resources in dataset_resources.items():
        for resource_path, resource_dict in resources.items():
            resource_dict['package_id'] = dataset_id
            with open(os.path.join(DEMO_DATA_PATH, resource_path), 'rb') as res_file:
                ckan.call_action(
                    'resource_create',
                    resource_dict,
                    files={'upload': res_file}
                )


def load_data(adr_url, apikey):
    ckan = ckanapi.RemoteCKAN(adr_url, apikey=apikey)

    load_users(ckan)
    orgs = load_organizations(ckan)
    load_harvesters(ckan, organizations_ids_dict=orgs)
    load_datasets(ckan)
    load_resources(ckan)


if __name__ == '__main__':
    load_data('http://ckan', "6011357f-a7f8-4367-a47d-8c2ab8059520")
