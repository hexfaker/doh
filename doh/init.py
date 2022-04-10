import random
from pathlib import Path

from .config import (
    Config,
    ConfigType,
    Context,
    Parameters,
    load_config,
    merge_models,
    save_config,
)


def init(context: Context) -> None:
    # TODO style-preserving config editing
    if (context.project_dir / ConfigType.GLOBAL.file_name()).is_file():
        current_config = load_config(context)
        update_config = Config.construct()
    else:
        current_config = Config(
            ssh_port=random.randint(22_000, 23_000),
            environment={"HOME": "$HOME"},
            hosts={"all": Parameters()},
        )
        update_config = current_config

    if context.hostname not in current_config.hosts:
        update_config.hosts[context.hostname] = Parameters()

    if current_config.ssh_port == 0:
        update_config.ssh_port = random.randint(22_000, 23_000)

    if current_config.use_local_config:
        if (
            update_config.is_nontrivial()
            or not Path(ConfigType.LOCAL.file_name()).is_file()
        ):
            local_config = load_config(
                context, ConfigType.LOCAL, interpolate_env=False
            )
            save_config(
                context,
                merge_models(local_config, update_config),
                ConfigType.LOCAL,
            )
    else:
        if (
            update_config.is_nontrivial()
            or not Path(ConfigType.GLOBAL.file_name()).is_file()
        ):
            global_config = load_config(
                context, ConfigType.GLOBAL, interpolate_env=False
            )
            save_config(
                context,
                merge_models(global_config, update_config),
                ConfigType.GLOBAL,
            )
