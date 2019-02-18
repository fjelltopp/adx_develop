import os
import subprocess
import sys
SUDO = os.environ.get('MEERKAT_SUDO', '')

compose_file = "adx.yml"
compose = ["docker-compose", "-f" , "docker-compose.yml", "-f", compose_file]

COMPOSE_PATH = os.path.abspath(os.path.dirname(__file__))


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
