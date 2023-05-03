from typing import List

import shlex
import subprocess
from pathlib import Path

import typer
from doh.agent import ensure_agent_present
from doh.config import Config, Context
from doh.docker import build_image, docker_run_args_from_project, run_docker_run

SSH_SERVER_KEYS_PATH = "/var/okteto/remote/authorized_keys"
SSH_SERVER_DEFAULT_PORT = 2222


def run_ssh_server(context: Context, build: bool) -> None:
    config = context.config
    if build:
        build_image(config, context)

    typer.secho(
        "Your SSH config is below. Append it to your ~/.ssh/config\n\n",
        fg=typer.colors.GREEN,
    )
    typer.secho(
        f"Host {context.environment_id}\n"
        f"    Hostname localhost\n"
        f"    Port {config.ssh_port}\n"
        f"    ProxyJump <this-server-ssh-hostname>\n"
        f"    # Some workarounds related to ssh server implementation we use\n"
        f"    HostKeyAlgorithms=+ssh-rsa\n"
        f"    RemoteCommand bash --login -i # bash can be replaced with whatever you want\n"
        f"    RequestTTY force\n",
        fg=typer.colors.BRIGHT_CYAN,
    )
    cmd = ["/doh/ssh-server"]

    if config.before_command:
        subprocess.run(shlex.split(config.before_command), check=True)

    run_args = docker_run_args_from_project(context)
    run_args += prepare_run_args_for_ssh_server(config, context)
    run_docker_run(run_args, context.image_name, cmd)

    if config.after_command:
        subprocess.run(shlex.split(config.after_command), check=True)


def prepare_run_args_for_ssh_server(
    config: Config, context: Context
) -> List[str]:
    if config.ssh_port == 0:
        typer.secho(
            "SSH port is not configured. Run `doh init`", fg=typer.colors.RED
        )
        raise typer.Exit()
    agent_path = ensure_agent_present()
    bin_mount_arg = ["--volume", f"{agent_path}:/doh:ro"]

    port_share_arg = [
        "--publish",
        f"127.0.0.1:{config.ssh_port}:{SSH_SERVER_DEFAULT_PORT}",
    ]

    res = bin_mount_arg + port_share_arg

    auth_keys_path = Path.home() / ".ssh/authorized_keys"

    if auth_keys_path.exists():
        res += ["--volume", f"{auth_keys_path}:{SSH_SERVER_KEYS_PATH}:ro"]

    return res
