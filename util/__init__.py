import os
import subprocess
import sys
from time import sleep

SUDO = os.environ.get('ADX_SUDO', '')

compose = ["docker-compose"]

COMPOSE_PATH = os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
    '..'
)

ADX_PATH = os.path.expanduser(os.environ.get(
    "ADX_PATH",
    "~/fjelltopp/adx"
))
PG_USER = os.environ.get('PG_USER', 'ckan')
CKAN_TEST_SQLALCHEMY_URL = os.environ.get("CKAN_TEST_SQLALCHEMY_URL", "postgresql://ckan_default:pass@db/ckan_test")
FJELLTOPP_PASSWORD = os.environ.get("FJELLTOPP_PASSWORD", "fjelltopp")
ADMIN_APIKEY = os.environ.get("ADMIN_APIKEY", "6011357f-a7f8-4367-a47d-8c2ab8059520")
CKAN_SITE_URL = os.environ.get("CKAN_SITE_URL", "http://adr.local")
SKIP_DB_RESTART = (os.environ.get("SKIP_DB_RESTART", 'false').lower() == 'true')


def call_command(args):
    """
    Run a shell command with proper error logging.
    """
    try:
        print(' '.join(args).strip())
        retcode = subprocess.call(
            ' '.join(args).strip(),
            shell=True,
            cwd=COMPOSE_PATH
        )
        if retcode != 0:
            print(f"Command not successful. Returned {retcode}", file=sys.stderr)
        return retcode
    except OSError as e:
        print(f"Execution failed: {e}", file=sys.stderr)


def up(args, extra_args):
    """
    Start the dev_env.

    Args:
        args (NameSpace): The known args NameSpace object returned by argsparse
        extra ([str]): A list of strings detailing any extra unkown args
            supplied by the user.
    """
    # Export environment variables for dev_env options.

    # Build the complete command
    up = ["up", "-d"]
    command = '"{}"'.format(' '.join(compose + up))

    # Run the command
    call_command([SUDO, 'sh', '-c', command])


def run_docker_compose(args, extra_args):
    """
    Run's a docker compose command in the compose folder. Is used for the
    dc, exec, logs, bash, stop, restart commands.

    Args:
        args (NameSpace): The known args NameSpace object returned by argsparse
        extra ([str]): A list of strings detailing any extra unkown args
            supplied by the user
    """
    sudo_dc = [SUDO] + compose
    if args.action == 'dc':
        call_command(sudo_dc + extra_args)
    elif args.action == 'exec':
        call_command(sudo_dc + ["exec"] + extra_args)
    elif args.action == 'logs':
        call_command(sudo_dc + ["logs", "-f", "--tail 500"] + extra_args)
    elif args.action == 'bash':
        call_command(sudo_dc + ["exec", args.container, "bash"])
    else:
        call_command(sudo_dc + [args.action] + extra_args)


def init(args, extra):
    print("Initializing ADR submodules...")
    call_command(['git submodule update --init'])


def setup(args, extra):
    """
    Initialises the parent directory to be the AIDS Data Repository code base folder.
    Optionally specify which manifest to use.
    """
    print('Setting up the ADX codebase...')
    print('This will destroy changes, resetting everything to the remote.')

    if input('SURE YOU WANT TO CONTINUE? (y/N) ').lower() in ['y', 'yes']:
        call_command(['git submodule foreach "git checkout development|| :"'])
        call_command(['git submodule foreach "git reset --hard  || :"'])
        print('ADX code synced')
        print('--SETUP COMPLETE--')


def init_ckan_db(args, extra):
    call_command(['docker exec -it ckan /wait-for-it.sh localhost:5000 --timeout=0 -- echo "CKAN ready"'])
    call_command(['docker exec -it ckan /usr/local/bin/ckan -c /etc/ckan/ckan.ini db init'])
    call_command(['docker exec -it ckan /usr/local/bin/ckan -c /etc/ckan/ckan.ini unaids initdb'])
    call_command(['docker exec -it ckan /usr/local/bin/ckan -c /etc/ckan/ckan.ini harvester initdb'])
    call_command(['docker exec -it ckan /usr/local/bin/ckan -c /etc/ckan/ckan.ini validation init-db'])
    call_command(['docker exec -it ckan /usr/local/bin/ckan -c /etc/ckan/ckan.ini datastore set-permissions | docker exec -i db psql -U ckan'])
    call_command(['docker exec -it ckan /usr/local/bin/ckan -c /etc/ckan/ckan.ini versions initdb'])
    call_command(['docker exec -it ckan /usr/local/bin/ckan -c /etc/ckan/ckan.ini pages initdb'])
    call_command(['docker exec -it ckan /usr/local/bin/ckan -c /etc/ckan/ckan.ini opendata-request init-db'])
    call_command(['docker exec -it ckan /usr/local/bin/ckan -c /etc/ckan/ckan.ini user add admin email=admin@localhost name=admin fullname=Admin job_title=chief affiliation=fjelltopp password={FJELLTOPP_PASSWORD} apikey=a4bf5640-e1b2-4141-8c22-f2b96b6df2c3'])
    call_command([f'docker exec db psql -U {PG_USER} -c "UPDATE public.user SET apikey = \'{ADMIN_APIKEY}\' WHERE name = \'admin\';"'])
    call_command(['docker exec -it ckan /usr/local/bin/ckan -c /etc/ckan/ckan.ini sysadmin add admin'])


def load_demo_data(args, extra):
    call_command(['docker exec -it ckan /wait-for-it.sh localhost:5000 --timeout=0 -- echo "CKAN ready"'])
    import util.ckan_loader as loader
    loader.load_data(f"{CKAN_SITE_URL}", ADMIN_APIKEY)


def reset_test_db(args, extra):
    if not SKIP_DB_RESTART:
        print('SKIP_DB_RESTART not set, restarting the db: ')
        call_command(['docker restart db'])
    else:
        print('SKIP_DB_RESTART set to True, skipping db restart. ')
    retries = 5

    while retries > 0:
        print('Waiting for database to be set up, {} tries left'.format(retries))
        ret_code = call_command([f'docker exec db psql -U {PG_USER} -c "select 1;" > /dev/null 2>&1'])
        if ret_code == 0:
            print('Database ready')
            break
        retries = retries - 1
        sleep(1)

    call_command([f'docker exec db psql -U {PG_USER} -c "CREATE USER ckan_default WITH PASSWORD \'pass\'"'])
    call_command([f'docker exec db psql -U {PG_USER} -c "CREATE USER datastore_default WITH PASSWORD \'pass\'"'])
    call_command([f'docker exec db psql -U {PG_USER} -c "DROP DATABASE IF EXISTS ckan_test;"'])
    call_command([f'docker exec db psql -U {PG_USER} -c "DROP DATABASE IF EXISTS datastore_test;"'])
    call_command([f'docker exec db psql -U {PG_USER} -c "CREATE DATABASE ckan_test OWNER ckan_default ENCODING \'utf-8\';"'])
    call_command([f'docker exec db psql -U {PG_USER} -c "CREATE DATABASE datastore_test OWNER ckan_default ENCODING \'utf-8\';"'])
    call_command([f'docker exec -e CKAN_SQLALCHEMY_URL="{CKAN_TEST_SQLALCHEMY_URL}"'
                  f' ckan /usr/local/bin/ckan -c /etc/ckan/test-core.ini datastore set-permissions | docker exec -i db psql -U {PG_USER}'])
    call_command([f'docker exec -e CKAN_SQLALCHEMY_URL="{CKAN_TEST_SQLALCHEMY_URL}"'
                  f' ckan /usr/local/bin/ckan -c /etc/ckan/test-core.ini db init'])


def run_tests(args, extra):
    extension_name = "ckanext-" + args.extension
    extension_path = "/usr/lib/adx/" + extension_name
    extension_sub_path = "/".join(extension_name.split("-", 1))
    # for cases like ckanext-ytp-requests repository which uses ytp_requests test directory internally
    extension_sub_path = extension_sub_path.replace("-", "_")
    retcode = call_command([
        f'docker exec {args.interaction} -e CKAN_SQLALCHEMY_URL={CKAN_TEST_SQLALCHEMY_URL} '
        f'ckan /usr/local/bin/ckan-pytest --capture=no --disable-warnings '
        f'--ckan-ini={extension_path}/test.ini '
        f'{extension_path}/{extension_sub_path}/tests '
        f'--log-level=WARNING '
    ] + extra)
    if retcode != 0:
        print("Tests not successful. Returned: " + str(retcode))
        sys.exit(retcode)
    else:
        print("Test finished with exit code: " + str(retcode))


def deploy_master(args, extra):
    call_command([
        "cat {}/adx_manifest/all.xml | {}/adx_deploy/deploy_master.bash".format(
            ADX_PATH,
            ADX_PATH
        )
    ])
