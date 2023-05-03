from typing import Dict, List, Optional, TypeVar

import collections.abc
import dataclasses
import getpass
import logging
import socket
from enum import Enum
from functools import cached_property
from pathlib import Path

import envtoml
import pydantic
import toml
from pydantic import BaseModel, Field
from toml import TomlPathlibEncoder

LOG = logging.getLogger(__name__)


def dict_merge(*args, add_keys=True):
    """Stolen from https://gist.github.com/angstwad/bf22d1822c38a92ec0a9#gistcomment-3305932"""
    assert len(args) >= 2, "dict_merge requires at least two dicts to merge"
    rtn_dct = args[0].copy()
    merge_dicts = args[1:]
    for merge_dct in merge_dicts:
        if add_keys is False:
            merge_dct = {
                key: merge_dct[key]
                for key in set(rtn_dct).intersection(set(merge_dct))
            }
        for k, v in merge_dct.items():
            if not rtn_dct.get(k):
                rtn_dct[k] = v
            elif isinstance(rtn_dct[k], dict) and isinstance(
                merge_dct[k], collections.abc.Mapping
            ):
                rtn_dct[k] = dict_merge(
                    rtn_dct[k], merge_dct[k], add_keys=add_keys
                )
            elif isinstance(v, list):
                for list_value in v:
                    if list_value not in rtn_dct[k]:
                        rtn_dct[k].append(list_value)
            else:
                rtn_dct[k] = v
    return rtn_dct


_ModelType = TypeVar("_ModelType", bound=BaseModel)


def merge_models(m1: _ModelType, m2: _ModelType) -> _ModelType:
    d1 = m1.dict()
    d2 = m2.dict(exclude_defaults=True)

    dm = dict_merge(d1, d2)
    return m1.construct(**dm)


class Parameters(pydantic.BaseModel):
    bind_paths: List[str] = []


class FakeHomeParameters(BaseModel):
    root: Path = Path(".doh/home")
    real_paths: List[str] = []


class Config(pydantic.BaseModel):
    hosts: Dict[str, Parameters] = {}
    workdir_from_host: bool = True
    ssh_port: int = 0
    image_build_command: str = "docker build . -t {image_name}"
    use_local_config: bool = False
    environment: Dict[str, str] = {}
    sh_cmd: str = "bash"
    fake_home: Optional[FakeHomeParameters] = FakeHomeParameters(
        root=Path("./.doh/home")
    )
    run_extra_args: List[str] = Field(default_factory=list)
    before_command: Optional[str] = None
    after_command: Optional[str] = None

    def is_nontrivial(self):
        return len(self.dict(exclude_unset=True)) > 0


@dataclasses.dataclass
class Context:
    project_name: str
    project_dir: Path
    hostname: str = socket.gethostname()
    username: str = getpass.getuser()

    @property
    def image_name(self):
        return f"{self.project_name}-{self.username}"

    @property
    def environment_id(self):
        return f"{self.project_name}__{self.hostname}"

    @cached_property
    def config(self):
        return load_final_config(self)

    @classmethod
    def create_for_path(cls, path: Path) -> "Context":
        path = path.resolve()
        return cls(project_dir=path, project_name=path.name.lower())

    @classmethod
    def create_for_cwd(cls) -> "Context":
        return cls.create_for_path(Path.cwd())


class ConfigType(Enum):
    LOCAL = "dohrc.local.toml"
    GLOBAL = "dohrc.toml"
    FULL = None

    def __init__(self, file_name: Optional[str] = None):
        self._file_name = file_name

    def file_name(self):
        if self._file_name is not None:
            return self._file_name
        raise NotImplemented


def load_config(
    context: Context,
    type: ConfigType = ConfigType.FULL,
    interpolate_env: bool = True,
) -> Config:
    if interpolate_env:
        load_fn = envtoml.load
    else:
        load_fn = toml.load

    if type in [ConfigType.FULL, ConfigType.GLOBAL]:
        conf_path = context.project_dir / ConfigType.GLOBAL.file_name()
        if conf_path.is_file():
            config = Config.construct(**load_fn(conf_path))
        else:
            config = Config()

    if (
        type == ConfigType.FULL and config.use_local_config
    ) or type == ConfigType.LOCAL:
        conf_path = context.project_dir / ConfigType.LOCAL.file_name()
        if conf_path.is_file():
            local_config = Config.construct(**load_fn(conf_path))
        else:
            local_config = Config()

        if type == ConfigType.LOCAL:
            config = local_config
        else:
            config = merge_models(config, local_config)

    if type == ConfigType.FULL:
        config = Config.parse_obj(config.dict(exclude_unset=True))

    LOG.debug(config)

    return config


def load_final_config(
    context: Context,
) -> Config:
    config = load_config(context)

    if "all" not in config.hosts:
        config.hosts["all"] = Parameters()

    if context.hostname in config.hosts:
        config.hosts["all"] = merge_models(
            config.hosts["all"], config.hosts[context.hostname]
        )

    config.hosts[context.hostname] = config.hosts["all"]

    return config


class TomlConfigEncoder(TomlPathlibEncoder):  # type: ignore
    pass


def save_config(context: Context, config: Config, type: ConfigType) -> None:
    conf_path = context.project_dir / type.file_name()

    if type == ConfigType.GLOBAL:
        dct = config.dict()
    else:
        dct = config.dict(exclude_defaults=True)

    with conf_path.open("w") as f:
        toml.dump(dct, f, encoder=TomlConfigEncoder())
