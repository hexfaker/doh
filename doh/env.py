from pathlib import Path

from platformdirs import PlatformDirs
from pydantic import BaseSettings


class Env(BaseSettings):
    config_path: Path
    cache_path: Path

    @staticmethod
    def get() -> "Env":
        pd = PlatformDirs("doh", False)
        return Env(
            config_path=pd.user_config_path, cache_path=pd.user_cache_path
        )
