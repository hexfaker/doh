import logging
import os
import shlex
import subprocess
from pathlib import Path
from typing import List

import typer

from doh.config import Config, Context, load_config

IMAGE_NAME_PLACEHOLDER = "{image_name}"

LOG = logging.getLogger(__name__)


def user_args():
    uid = os.getuid()
    gid = os.getgid()

    return [f"--user {uid}:{gid}"]


def volume_args(config: Config, context: Context) -> List[str]:
    volumes = []
    if context.hostname in config.hosts:
        host_bind_paths = config.hosts[context.hostname].bind_paths
        resolved_paths_volumes = [
            f"{os.path.realpath(source)}:{target}"
            for source, target in map(lambda s: s.split(":"), host_bind_paths)
        ]
        volumes += [f"--volume {v}" for v in resolved_paths_volumes]
    volumes.append(f"--volume {context.cwd}:{context.cwd}")

    return volumes


def get_default_args(config: Config, context: Context) -> List[str]:
    res = [f"--ipc=host --pid=host"]

    if config.workdir_from_host:
        res.append(f"--workdir '{context.cwd}'")

    return res


def connect_home(config: Config, context: Context) -> List[str]:
    home_path = os.environ["HOME"]

    return [f"--volume {home_path}:{home_path}", f"-e HOME={home_path}"]


def prepare_for_ssh_server(config: Config, context: Context) -> List[str]:
    if config.ssh_port == 0:
        typer.secho("SSH port is not configured. Run `doh init`", fg=typer.colors.RED)
        raise typer.Exit()

    bin_package_dir = (Path(__file__).parent / "bin").resolve()
    bin_mount_arg = f"--volume {bin_package_dir}:/.doh_bin/:ro"

    port_share_arg = (
        f"--publish 127.0.0.1:{config.ssh_port}:{SSH_SERVER_DEFAULT_PORT}"
    )

    res = [bin_mount_arg, port_share_arg]

    auth_keys_path = Path.home() / ".ssh/authorized_keys"
    if auth_keys_path.exists():
        res.append(f"--volume {auth_keys_path}:{SSH_SERVER_KEYS_PATH}:ro")

    return res


def form_cli_args(
    config: Config, context: Context, extra_args: List[str]
) -> str:
    run_args = ["--rm -it"]
    run_args += user_args()
    run_args += volume_args(config, context)
    run_args += get_default_args(config, context)
    run_args += connect_home(config, context)
    run_args += prepare_for_ssh_server(config, context)

    run_args = " ".join(run_args)
    cli_args = f"run {run_args} {context.project_name} {' '.join(extra_args)}"
    LOG.debug(cli_args)
    return cli_args


def run_docker_cli(args: str, exec: bool = False) -> None:
    args = ["docker"] + shlex.split(args)

    if exec:
        os.execv(args[0], args)
    else:
        subprocess.run(args)


SSH_SERVER_KEYS_PATH = "/var/okteto/remote/authorized_keys"
SSH_SERVER_DEFAULT_PORT = 2222


def build_image(config: Config, context: Context):
    image_name = f"{context.image_name}:latest"

    if IMAGE_NAME_PLACEHOLDER not in config.image_build_command:
        LOG.warning(
            f"Image build command doesn't contain {IMAGE_NAME_PLACEHOLDER}, container launch will likely be incorrect"
        )

    build_cmd = config.image_build_command.replace(
        IMAGE_NAME_PLACEHOLDER, image_name
    )

    subprocess.run(shlex.split(build_cmd), check=True)


def exec_in_docker(build, cmd, context):
    config = load_config()
    if build:
        build_image(config, context)
    run_docker_cli(form_cli_args(config, context, cmd))
