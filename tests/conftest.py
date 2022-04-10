from pathlib import Path

from doh.config import Context
from pytest import fixture


@fixture
def context(tmpdir):
    return Context.create_for_path(Path(tmpdir))
