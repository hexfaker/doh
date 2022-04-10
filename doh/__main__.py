from typing import List

import logging

import typer
from doh.ssh import run_ssh_server
from doh.utils import setup_logging

from .config import Context, load_final_config
from .docker import build_image, form_cli_args, run_docker_cli
from .init import init

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
    run_docker_cli(form_cli_args(config, context, cmd))


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


@app.command()
def ssh(build: bool = True) -> None:
    run_ssh_server(Context.create_for_cwd(), build)


if __name__ == "__main__":
    app()
