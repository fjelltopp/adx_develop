import os
import subprocess
import sys
from . import repo

SUDO = os.environ.get('MEERKAT_SUDO', '')

compose = ["docker-compose"]

COMPOSE_PATH = os.path.abspath(os.path.dirname(__file__))
# If you want to fetch containers using https, you should set this env var to
# https://github.com/meerkat-code/meerkat.git
MANIFEST_URL = os.environ.get(
    'MEERKAT_MANIFEST',
    'git@github.com:fjelltopp/adx_manifest.git'
)
DEFAULT_MANIFEST = 'default.xml'


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
        if retcode is not 0:
            print >> sys.stderr, "Command not successful. Returned", retcode
    except OSError as e:
        print >> sys.stderr, "Execution failed:", e


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
        call_command(sudo_dc + ["logs", "-f"] + extra_args)
    elif args.action == 'bash':
        call_command(sudo_dc + ["exec", args.container, "bash"])
    else:
        call_command(sudo_dc + [args.action] + extra_args)


def run_repo(args, extra):
    """
    Run's a Google Repo command by just forwarding the supplied args to the
    main() function of the Google Repo script.

    Args:
        args (NameSpace): The known args NameSpace object returned by argsparse
        extra ([str]): A list of strings detailing any extra unkown args
            supplied by the user
    """
    if args.action == "repo":
        print(extra)
        repo.main(extra)
    else:
        repo.main([args.action] + extra)


def init(args, extra):
    print("Initializing the ADX codebase...")
    manifest = args.manifest if args.manifest else DEFAULT_MANIFEST
    repo.main(['init', '-u', MANIFEST_URL, '-m', manifest])
    print("ADX status:")
    repo.main(['status'])


def setup(args, extra):
    """
    Initialises the parent directory to be the Meerkat code base folder.
    Optionally specify which manifest to use.
    """
    print('Setting up the ADX codebase...')
    print('This will destroy changes, resetting everything to the remote.')

    if raw_input('SURE YOU WANT TO CONTINUE? (y/N) ').lower() in ['y', 'yes']:
        manifest = args.manifest if args.manifest else DEFAULT_MANIFEST
        repo.main(['init', '-u', MANIFEST_URL, '-m', manifest])
        repo.main(['sync', '--force-sync'])
        print('ADX code synced')
        repo.main(['forall', '-c', 'git', 'checkout', 'master'])
        repo.main(['forall', 'ckan', '-c', 'git', 'checkout', 'refs/tags/ckan-2.8.2'])
        repo.main(['forall', 'ckanext-scheming', '-c', 'git', 'checkout', 'validator'])
        repo.main(['status'])
        print('--SETUP COMPLETE--')

def init_ckan_db(args, extra):
    call_command(['docker exec ckan /usr/local/bin/ckan-paster --plugin=ckan datastore set-permissions -c /etc/ckan/production.ini | docker exec -i db psql -U ckan'])
    call_command(['docker exec ckan /usr/local/bin/ckan-paster --plugin=ckanext-ytp-request initdb -c /etc/ckan/production.ini'])
    call_command(['docker exec -it ckan /usr/local/bin/ckan-paster --plugin=ckanext-harvest harvester initdb -c /etc/ckan/production.ini'])
    call_command(['docker exec -it ckan /usr/local/bin/ckan-paster --plugin=ckan sysadmin -c /etc/ckan/production.ini add admin'])

