from typing import Any, List, Union

import logging
import os
import shlex
import subprocess
from pathlib import Path

import typer
from click.exceptions import Exit
from doh.config import Config, Context

IMAGE_NAME_PLACEHOLDER = "{image_name}"

LOG = logging.getLogger(__name__)


def user_args():
    uid = os.getuid()
    gid = os.getgid()

    return ["--user", f"{uid}:{gid}"]


def volume_args(config: Config, context: Context) -> List[str]:
    volumes: List[Any] = []
    resolved_paths_volumes = [
        f"{os.path.realpath(source)}:{target}"
        for source, target in map(lambda s: s.split(":"), config.bind_paths)
    ]
    volumes += sum((["--volume", v] for v in resolved_paths_volumes), [])
    volumes += ["--volume", f"{context.project_dir}:{context.project_dir}"]

    return volumes


def get_default_args(config: Config, context: Context) -> List[str]:
    res = ["--ipc=host", "--pid=host", "--hostname", context.environment_id]

    if config.workdir_from_host:
        res += ["--workdir", str(context.project_dir)]

    return res


def env_args(config: Config, context: Context) -> List[str]:
    return sum(
        (["--env", f"{k}={v}"] for k, v in config.environment.items()), []
    )


def prepare_home_args(config: Config, context: Context) -> List[str]:
    res: List[str] = []
    if config.fake_home is None:
        return res
    fake_home_path = config.fake_home.root.resolve()
    real_home_path = Path.home()

    if not fake_home_path.is_dir():
        LOG.info("Initialize fake home")
        fake_home_path.mkdir(parents=True)

    res += ["--volume", f"{fake_home_path}:{real_home_path}"]
    res += ["--env", f"HOME={real_home_path}"]

    for f in config.fake_home.real_paths:
        full_f = real_home_path / f

        if not full_f.exists():
            typer.secho(f"{full_f} do not exist, can't start container")
            raise Exit(1)

        # Prevent required paths creation with root ownership
        if full_f.is_file():
            (fake_home_path / f).touch(exist_ok=True)
        elif full_f.is_dir():
            (fake_home_path / f).mkdir(exist_ok=True)

        res += ["--volume", f"{full_f}:{full_f}"]

    return res


def docker_run_args_from_project(
    project: Context, request_tty: bool = True
) -> List[str]:
    config = project.config
    run_args = ["--rm"]

    if request_tty:
        run_args += ["--tty", "--interactive"]
    run_args += user_args()
    run_args += volume_args(config, project)
    run_args += get_default_args(config, project)
    run_args += prepare_home_args(config, project)
    run_args += env_args(config, project)
    run_args += config.run_extra_args
    return run_args


def run_docker_cli(args: str) -> None:
    LOG.debug(args)
    argv = ["docker"] + shlex.split(args)

    subprocess.run(argv)


def run_docker_run(
    run_args: List[str],
    image_name: str,
    cmd: Union[List[str], str],
) -> None:
    cmd = shlex.join(map(str, cmd)) if not isinstance(cmd, str) else cmd
    run_args_cat = shlex.join(map(str, run_args))
    run_docker_cli(f"run {run_args_cat} {image_name} {cmd}")


def build_image(config: Config, context: Context) -> None:
    image_name = f"{context.image_name}:latest"

    if IMAGE_NAME_PLACEHOLDER not in config.image_build_command:
        LOG.warning(
            f"Image build command doesn't contain {IMAGE_NAME_PLACEHOLDER}, container launch will likely be incorrect"
        )

    build_cmd = config.image_build_command.replace(
        IMAGE_NAME_PLACEHOLDER, image_name
    )

    subprocess.run(shlex.split(build_cmd), check=True)
