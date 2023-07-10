from doh.commands.init import init
from doh.config import Config, Context, load_config


def test_init_empty(context: Context) -> None:
    init(context)

    after_init = load_config(context)
    expected_config = Config()

    assert {p.name for p in context.project_dir.glob("*")} == {
        "dohrc.toml",
        "dohrc.local.toml",
        "doh.env",
        "doh.local.env",
        ".gitignore",
        "Dockerfile",
    }

    assert after_init.ssh_port != 0

    expected_config.ssh_port = after_init.ssh_port
    expected_config.environment = {"HOME": "$HOME"}

    assert after_init == expected_config
