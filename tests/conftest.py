import os
from pathlib import Path

from doh.config import Context
from doh.env import Env
from pytest import fixture


@fixture
def context(tmpdir):
    return Context.create_for_path(Path(tmpdir))


@fixture(autouse=True)
def test_env(tmp_path):
    old = os.environ.get("HOME", None)
    try:
        os.environ["HOME"] = str(tmp_path)
        yield Env.get()
    finally:
        if old:
            os.environ["HOME"] = old
        else:
            del os.environ["HOME"]
