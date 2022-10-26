import json

from doh.config import Config, Context
from doh.docker import docker_run_args_from_project


def test_extra_args(context: Context):
    extra_args = ["--runtime nvidia", "--gpus=all"]
    (context.project_dir / "dohrc.toml").write_text(
        "run_extra_args = %s" % json.dumps(extra_args)
    )

    final_args = docker_run_args_from_project(context)

    assert all(a in final_args for a in extra_args)


def test_extra_args_empty(context: Context):
    (context.project_dir / "dohrc.toml").write_text(
        "use_local_config=true"  # Emulate real config without extra args
    )

    docker_run_args_from_project(context)

    # No crashes yay
