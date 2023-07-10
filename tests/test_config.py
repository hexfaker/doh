from pathlib import Path

from doh.config import load_config  # save_config,

# def test_save_load_cycle(context: Context) -> None:
#     test_config = Config(
#         workdir_from_host=False,
#         ssh_port=1024,
#         image_build_command="build_foo",
#         use_local_config=True,
#         environment={"FOO": "BAR"},
#         sh_cmd="foobar",
#         fake_home=FakeHomeParameters(root=Path(".foo/home")),
#     )
#     save_config(context, test_config, ConfigType.GLOBAL)
#     loaded_config = load_config_file(context)
#
#     assert loaded_config == test_config
#     assert loaded_config != Config()


def test_load_user_config(context):
    user_rc_path = Path.home() / ".config/doh/rc.toml"
    user_rc_path.parent.mkdir(exist_ok=True, parents=True)

    user_rc_path.write_text("[environment]\n" 'USER_VAR="foo"\n')

    project_rc = context.project_dir / "dohrc.toml"
    project_rc.write_text("[environment]\n" 'PROJECT_VAR="bar"\n')

    config = load_config(context)

    assert config.environment["USER_VAR"] == "foo"
    assert config.environment["PROJECT_VAR"] == "bar"


def test_load_extra_configs(context):
    project_rc = context.project_dir / "dohrc.toml"
    project_rc.write_text('extra_config_paths = ["extra_1.toml"]')

    (context.project_dir / "extra_1.toml").write_text(
        'extra_config_paths = ["extra_2.toml"]\n'
        "[environment]\n"
        "EXTRA_1_VAR=1\n"
    )

    (context.project_dir / "extra_2.toml").write_text(
        "[environment]\n" "EXTRA_2_VAR=2\n"
    )

    config = load_config(context)

    assert config.environment["EXTRA_1_VAR"] == "1"
    assert config.environment["EXTRA_2_VAR"] == "2"
