import random
from pathlib import Path

from .config import (
    Config,
    ConfigType,
    Context,
    Parameters,
    load_config,
    merge_models, save_config,
)


def init(context: Context) -> None:
    # TODO style-preserving config editing
    if Path("./dohrc.toml").is_file():
        current_config = load_config()
        update_config = Config.construct()
    else:
        current_config = Config(ssh_port=random.randint(22_000, 23_000))
        update_config = current_config

    if context.hostname not in current_config.hosts:
        update_config.hosts[context.hostname] = Parameters()

    if current_config.ssh_port == 0:
        update_config.ssh_port = random.randint(22_000, 23_000)

    if current_config.use_local_config:
        local_config = load_config(ConfigType.LOCAL)
        save_config(merge_models(local_config, update_config), ConfigType.LOCAL)
    else:
        save_config(merge_models(current_config, update_config), ConfigType.GLOBAL)

