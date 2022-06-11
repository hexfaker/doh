from typing import List

import logging
from pathlib import Path

import typer
from doh.agent import ensure_agent_present
from doh.commands import kernel
from doh.commands.init import init
from doh.commands.ssh import run_ssh_server
from doh.utils import setup_logging

from .config import Context, load_final_config
from .docker import build_image, docker_run_args_from_project, run_docker_run

setup_logging()

LOG = logging.getLogger(__file__)
app = typer.Typer()


@app.command(
    name="exec",
    context_settings={"ignore_unknown_options": True},
    add_help_option=False,
)
def exec_cmd(
    cmd: List[str],
    build: bool = True,
) -> None:
    context = Context.create_for_cwd()
    config = load_final_config(context)
    if build:
        build_image(config, context)
    run_docker_run(
        docker_run_args_from_project(config, context), context.image_name, cmd
    )


@app.command(
    name="init",
    help="Creates dohrc.toml if doesn't exist yet, populates it with global and current host section",
)
def init_cmd():
    init(Context.create_for_cwd())


@app.command()
def sh():
    config = load_final_config(Context.create_for_cwd())
    exec_cmd([config.sh_cmd])


@app.command(hidden=True)
def download_ssh():
    ensure_agent_present()


@app.command()
def ssh(build: bool = True) -> None:
    run_ssh_server(Context.create_for_cwd(), build)


@app.command()
def kernel_install(language: str = "python"):
    project = Context.create_for_cwd()
    kernel.install(project, language)


@app.command()
def kernel_run(
    project_root: Path = typer.Argument(..., dir_okay=True),
    kernel_conn_spec_path: Path = typer.Argument(..., file_okay=True),
    build: bool = True,
):
    kernel.run_kernel(
        Context.create_for_path(project_root), kernel_conn_spec_path, build
    )


if __name__ == "__main__":
    app()
