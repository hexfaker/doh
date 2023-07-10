from typing import Dict, List, Optional, Set, Tuple, TypeVar

import collections.abc
import dataclasses
import getpass
import logging
import os
import socket
from functools import cached_property
from pathlib import Path

import dotenv
import pydantic
import toml
from dotenv.variables import parse_variables
from pydantic import BaseModel, Extra, Field
from toml import TomlPathlibEncoder

from .env import Env

LOG = logging.getLogger(__name__)

LOCAL_ENV_NAME = "doh.local.env"
MAIN_ENV_NAME = "doh.env"

MAIN_CONF_NAME = "dohrc.toml"
LOCAL_CONF_NAME = "dohrc.local.toml"

TOML_DECODER = toml.TomlDecoder()


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


class FakeHomeParameters(BaseModel):
    root: Path = Path(".doh/home")
    real_paths: List[str] = []


class ConfigPart(BaseModel):
    class Config:
        extra = Extra.ignore

    extra_config_paths: List[Path] = pydantic.Field(default_factory=list)


class Config(pydantic.BaseModel):
    workdir_from_host: bool = True
    ssh_port: Optional[int] = None
    image_build_command: str = "docker build . -t {image_name}"
    environment: Dict[str, str] = pydantic.Field(default_factory=dict)
    sh_cmd: str = "bash"
    fake_home: Optional[FakeHomeParameters] = FakeHomeParameters(
        root=Path("./.doh/home")
    )
    run_extra_args: List[str] = Field(default_factory=list)
    before_command: Optional[str] = None
    after_command: Optional[str] = None
    bind_paths: List[str] = []
    extra_config_paths: List[Path] = pydantic.Field(default_factory=list)

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
        return load_config(self)

    @classmethod
    def create_for_path(cls, path: Path) -> "Context":
        path = path.resolve()
        return cls(project_dir=path, project_name=path.name.lower())

    @classmethod
    def create_for_cwd(cls) -> "Context":
        return cls.create_for_path(Path.cwd())


def _load_env(project: Context) -> Dict[str, str]:
    env: Dict[str, Optional[str]] = {
        "HOSTNAME": project.hostname,
        "USER": project.username,
        "DOH_PROJECT_ROOT": str(project.project_dir),
        "DOH_ENVIRONMENT_ID": project.environment_id,
        "DOH_PROJECT_NAME": project.project_name,
    }

    paths = [
        Env.get().config_dir / MAIN_ENV_NAME,
        project.project_dir / MAIN_ENV_NAME,
        project.project_dir / LOCAL_ENV_NAME,
    ]

    for p in paths:
        if p.exists():
            env.update(dotenv.dotenv_values(p))
            LOG.debug("Loaded %s, current env=%s", str(p), env)
        else:
            LOG.debug("%s not found, skipping", str(p))

    env.update(os.environ)

    return {k: v for k, v in env.items() if v is not None}


def _load_part(
    current_config: Config, part_path: Path, env: Dict[str, str]
) -> Tuple[Config, List[Path]]:
    LOG.debug("Current config=%s env=%s", current_config, env)
    if not part_path.exists():
        LOG.debug("Config %s not exist", part_path)
        return current_config, []

    LOG.debug("Loading %s", part_path)

    part_dict = toml.load(part_path)

    part_dict = _expand_env_deep(part_dict, env)

    LOG.debug("Loaded %s: %s", part_path, part_dict)
    part = ConfigPart.parse_obj(part_dict)
    current_config = merge_models(current_config, Config.construct(**part_dict))
    extra_paths = part.extra_config_paths
    return current_config, extra_paths


def load_config(project: Context) -> Config:
    final_config = Config()
    paths_to_load = {
        Env.get().config_dir / "rc.toml",
        project.project_dir / MAIN_CONF_NAME,
    }
    env = _load_env(project)

    paths_loaded: Set[Path] = set()

    LOG.debug("Config loading started")

    while paths_loaded != paths_to_load:
        diff = paths_to_load - paths_loaded

        # filter from original list to preserve order
        next_paths = [p for p in paths_to_load if p in diff]

        for part_path in next_paths:
            final_config, extra_paths = _load_part(final_config, part_path, env)
            LOG.debug("More config paths %s", extra_paths)
            extra_paths = [
                p if p.is_absolute() else project.project_dir / p
                for p in extra_paths
            ]
            paths_to_load.update(extra_paths)

        paths_loaded.update(diff)

    final_config, extra_paths = _load_part(
        final_config, project.project_dir / LOCAL_CONF_NAME, env
    )

    if len(extra_paths) > 0:
        LOG.warning(
            "dohrc.local.toml contains some extra paths. They will be ignored"
        )

    LOG.debug(
        "Config loading completed: config=%s. Validating...", final_config
    )
    final_config = Config.parse_obj(final_config.dict())
    LOG.debug("Final config: config=%s", final_config)
    return final_config


class TomlConfigEncoder(TomlPathlibEncoder):  # type: ignore
    pass


def save_config(
    config: Config, path: Path, non_default_only: bool = True
) -> None:
    dct = config.dict(exclude_defaults=non_default_only)

    with path.open("w") as f:
        toml.dump(dct, f, encoder=TomlConfigEncoder())


def _expand_env_deep(item, env, parse=True):
    if isinstance(item, str):
        item = _expand_env(env, item)

        if not parse:
            return item

        # Try parsing result string value into something else
        try:
            item, _ = TOML_DECODER.load_value(item)
        except ValueError:
            pass
        return item
    elif isinstance(item, dict):
        return {
            _expand_env_deep(k, env, parse=False): _expand_env_deep(v, env)
            for k, v in item.items()
        }
    elif isinstance(item, list):
        return [_expand_env_deep(v, env) for v in item]
    else:
        return item


def _expand_env(env, item):
    return "".join(atom.resolve(env) for atom in parse_variables(item))
