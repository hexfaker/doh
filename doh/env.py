from pathlib import Path

from platformdirs import PlatformDirs
from pydantic import BaseSettings


class Env(BaseSettings):
    config_dir: Path
    cache_dir: Path

    @staticmethod
    def get() -> "Env":
        pd = PlatformDirs("doh", False)
        return Env(config_dir=pd.user_config_path, cache_dir=pd.user_cache_path)
