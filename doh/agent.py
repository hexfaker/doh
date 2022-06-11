import hashlib
import shutil
from pathlib import Path

from .docker import run_docker_run, user_args
from .env import Env

SSH_SERVER_IMAGE_TAG = "okteto/remote:0.4.2"
SSH_SERVER_EXECUTABLE_PATH = "/usr/local/bin/remote"
CACHE_KEY = hashlib.md5(
    f"doh-okteto-cache-{SSH_SERVER_IMAGE_TAG}".encode(), usedforsecurity=False
).hexdigest()


def build_cache_key_path() -> Path:
    return agent_path() / CACHE_KEY


def agent_path() -> Path:
    return Env.get().cache_path / "agent"


def is_cache_valid():
    return build_cache_key_path().is_file()


def download_ssh_server() -> None:
    key = build_cache_key_path()

    shutil.rmtree(key.parent, ignore_errors=True)
    key.parent.mkdir(exist_ok=True, parents=True)

    run_args = [
        "--rm",
        *user_args(),
        "--volume",
        f"{key.parent}:/doh",
    ]

    run_docker_run(
        run_args,
        SSH_SERVER_IMAGE_TAG,
        ["cp", SSH_SERVER_EXECUTABLE_PATH, "/doh/ssh-server"],
    )
    key.touch()


def ensure_agent_present() -> Path:
    if not is_cache_valid():
        download_ssh_server()
    return agent_path()
