import logging
from typing import List

import typer

from doh.utils import setup_logging
from .config import Context, load_config
from .docker import exec_in_docker
from .init import init

setup_logging()

LOG = logging.getLogger(__file__)
app = typer.Typer()

@app.command(
    context_settings={"ignore_unknown_options": True}, add_help_option=False
)
def exec(
    cmd: List[str],
    build: bool = True,
) -> None:
    context = Context()
    exec_in_docker(build, cmd, context)


@app.command(name="init", help="Creates dohrc.toml if doesn't exist yet, populates it with global and current host section")
def init_cmd():
    init(Context())

@app.command()
def sh():
    exec(["bash --norc"])


@app.command()
def ssh():
    context = Context()
    config = load_config()
    typer.secho("Your SSH config is below. Append it to your ~/.ssh/config\n\n", fg=typer.colors.GREEN)
    typer.secho(
        f"Host {context.project_name}__{context.hostname}\n"
        f"    Hostname localhost\n"
        f"    Port {config.ssh_port}\n"
        f"    ProxyJump <this-server-ssh-hostname>\n"
        f"    HostKeyAlgorithms=+ssh-rsa\n",
        fg=typer.colors.BRIGHT_CYAN
    )
    exec(["/.doh_bin/ssh-server"])


if __name__ == "__main__":
    app()
