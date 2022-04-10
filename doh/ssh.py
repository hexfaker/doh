import typer
from doh.config import Context, load_final_config
from doh.docker import build_image, form_cli_args, run_docker_cli


def run_ssh_server(context: Context, build: bool) -> None:
    config = load_final_config(context)
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
    cmd = ["/.doh_bin/ssh-server"]
    run_docker_cli(form_cli_args(config, context, cmd, ssh=True))
