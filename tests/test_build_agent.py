from doh.agent import build_cache_key_path, ensure_agent_present
from doh.env import Env


def test_ssh_cache(test_env: Env):
    ensure_agent_present()

    cache_key = build_cache_key_path()
    assert cache_key.exists()
    assert (cache_key.parent / "ssh-server").exists()


def test_cache_invalidation(test_env: Env):
    agent_path = test_env.cache_path / "agent"
    agent_path.mkdir(parents=True)

    server_path = agent_path / "ssh-server"
    OLD_VERSION_BIN = b"OLD"
    server_path.write_bytes(OLD_VERSION_BIN)

    ensure_agent_present()

    assert server_path.read_bytes() != OLD_VERSION_BIN
