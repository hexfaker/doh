from pathlib import Path

from doh.config import (
    Config,
    ConfigType,
    Context,
    FakeHomeParameters,
    load_config,
    save_config,
)


def test_save_load_cycle(context: Context) -> None:
    test_config = Config(
        workdir_from_host=False,
        ssh_port=1024,
        image_build_command="build_foo",
        use_local_config=True,
        environment={"FOO": "BAR"},
        sh_cmd="foobar",
        fake_home=FakeHomeParameters(root=Path(".foo/home")),
    )
    save_config(context, test_config, ConfigType.GLOBAL)
    loaded_config = load_config(context)

    assert loaded_config == test_config
    assert loaded_config != Config()
