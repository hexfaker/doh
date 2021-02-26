import logging
import os
import shlex
import subprocess
from pathlib import Path
import socket
from typing import Dict, List

import pydantic
import toml
import typer

LOG = logging.getLogger(__file__)
logging.basicConfig(level=logging.DEBUG)


class Parameters(pydantic.BaseModel):
    bind_paths: List[str] = []


class Config(pydantic.BaseModel):
    hosts: Dict[str, Parameters] = {}
    workdir_from_host: bool = True


class Context(pydantic.BaseModel):
    hostname: str = socket.gethostname()
    cwd: Path = Path.cwd()
    project_name: str = Path.cwd().name


def load_config():
    conf_path = Path.cwd() / "dohrc.toml"
    if conf_path.is_file():
        config = Config.parse_obj(toml.load(conf_path))
    else:
        config = Config()
    LOG.debug(config)
    return config


app = typer.Typer()


def user_args():
    uid = os.getuid()
    gid = os.getgid()

    return [f"--user {uid}:{gid}"]


def volume_args(config: Config, context: Context):
    volumes = []
    if context.hostname in config.hosts:
        volumes += [f"--volume {v}" for v in config.hosts[context.hostname].bind_paths]
    volumes.append(f"--volume {context.cwd}:{context.cwd}")

    return volumes


def get_default_args(config: Config, context: Context):
    res = [
        f"--runtime=nvidia --ipc=host --network=host --pid=host"
    ]

    if config.workdir_from_host:
        res.append(f"--workdir '{context.cwd}'")

    return res


def connect_home(config: Config, context: Context):
    home_path = os.environ["HOME"]

    return [
        f"--volume {home_path}:{home_path}",
        f"-e HOME={home_path}"
    ]


def form_cli_args(config: Config, context: Context, extra_args: List[str]):
    run_args = ["--rm -it"]
    run_args += user_args()
    run_args += volume_args(config, context)
    run_args += get_default_args(config, context)
    run_args += connect_home(config, context)

    run_args = ' '.join(run_args)
    cli_args = f"run {run_args} {context.project_name} {' '.join(extra_args)}"
    LOG.debug(cli_args)
    return cli_args


def run_docker_cli(args: str, exec=False):
    args = ["docker"] + shlex.split(args)

    if exec:
        os.execv(args[0], args)
    else:
        subprocess.run(args)


@app.command(context_settings={"ignore_unknown_options": True})
def run(default_cmd: bool = False, extra_args: List[str] = []):
    if not default_cmd:
        extra_args = ["bash --norc", *extra_args]

    context = Context()
    image_name = f"{context.project_name}:latest"

    run_docker_cli(f"build . -t {image_name}")
    config = load_config()
    run_docker_cli(
        form_cli_args(config, context, extra_args)
    )


if __name__ == "__main__":
    app()
