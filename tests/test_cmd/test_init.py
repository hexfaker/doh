from doh.commands.init import init
from doh.config import Config, Context, Parameters, load_config


def test_init_empty(context: Context) -> None:
    init(context)

    after_init = load_config(context, interpolate_env=False)
    expected_config = Config()

    assert after_init.ssh_port != 0

    expected_config.ssh_port = after_init.ssh_port
    expected_config.environment = {"HOME": "$HOME"}
    expected_config.hosts = {
        "all": Parameters(),
        context.hostname: Parameters(),
    }

    assert after_init == expected_config
