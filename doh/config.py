import logging
import random
import collections.abc
import socket
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional
import getpass

import pydantic
import toml
from pydantic import BaseModel

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
            elif k in rtn_dct and type(v) != type(rtn_dct[k]):
                raise TypeError(
                    f"Overlapping keys exist with different types: original is {type(rtn_dct[k])}, new value is {type(v)}"
                )
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


def merge_models(m1: BaseModel, m2: BaseModel):
    d1 = m1.dict()
    d2 = m2.dict(exclude_defaults=True)

    dm = dict_merge(d1, d2)
    return m1.construct(**dm)


class Parameters(pydantic.BaseModel):
    bind_paths: List[str] = []


class Config(pydantic.BaseModel):
    hosts: Dict[str, Parameters] = {}
    workdir_from_host: bool = True
    ssh_port: int = 0
    image_build_command: str = "docker build . -t {image_name}"
    use_local_config: bool = False

    def is_nontrivial(self):
        return len(self.dict(exclude_unset=True)) == 0


class Context(pydantic.BaseModel):
    hostname: str = socket.gethostname()
    cwd: Path = Path.cwd()
    project_name: str = Path.cwd().name
    username: str = getpass.getuser()

    @property
    def image_name(self):
        return f"{self.project_name}-{self.username}"


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


def load_config(type: ConfigType = ConfigType.FULL) -> Config:
    if type in [ConfigType.FULL, ConfigType.GLOBAL]:
        conf_path = Path.cwd() / ConfigType.GLOBAL.file_name()
        if conf_path.is_file():
            config = Config.construct(**toml.load(conf_path))
        else:
            config = Config()

    if (
        type == ConfigType.FULL and config.use_local_config
    ) or type == ConfigType.LOCAL:
        conf_path = Path.cwd() / ConfigType.LOCAL.file_name()
        if conf_path.is_file():
            local_config = Config.construct(**toml.load(conf_path))
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


def save_config(config: Config, type: ConfigType) -> None:
    conf_path = Path.cwd() / type.file_name()

    if type == ConfigType.GLOBAL:
        dct = config.dict()
    else:
        dct = config.dict(exclude_defaults=True)

    with conf_path.open("w") as f:
        toml.dump(dct, f)