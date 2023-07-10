import logging
import shutil
from pathlib import Path

from ...config import (
    LOCAL_CONF_NAME,
    LOCAL_ENV_NAME,
    MAIN_CONF_NAME,
    MAIN_ENV_NAME,
    Config,
    Context,
    load_config,
    save_config,
)
from ...utils.misc import generate_doh_port

_LOG = logging.getLogger(__name__)


def init(project: Context) -> None:
    project_dir = project.project_dir.absolute()
    main_config_path = project_dir / MAIN_CONF_NAME
    first_init = not main_config_path.is_file()

    if first_init:
        _LOG.info("Initializing project from scratch in %s", str(project_dir))

        if not project_dir.exists():
            project_dir.mkdir(exist_ok=True, parents=True)

        if not (dockerfile_path := project_dir / "Dockerfile").is_file():
            _LOG.info("Create sample Dockerfile")
            shutil.copy(Path(__file__).parent / "Dockerfile", dockerfile_path)

        config = Config(environment={"HOME": "$HOME"})
        save_config(config, main_config_path, False)

        (project_dir / MAIN_ENV_NAME).write_text(
            "# Default environment variables\n" "# SOME_VAR=some_value\n"
        )

        _add_locals_to_gitignore(project_dir)

    else:
        _LOG.info("Existing project detected in %s", str(project_dir))
        config = load_config(project)

    local_config_path = project_dir / LOCAL_CONF_NAME

    if not local_config_path.is_file():
        _LOG.info(f"Creating local config {LOCAL_CONF_NAME}")
        local_config = Config()
        if config.ssh_port is None:
            local_config.ssh_port = generate_doh_port()

        save_config(local_config, local_config_path)

        (project_dir / LOCAL_ENV_NAME).write_text(
            "# Local environment variables (ignored it in git)\n"
            "# SOME_VAR=some_value\n"
        )
    else:
        _LOG.info(f"Local config {LOCAL_CONF_NAME} already exist")


def _add_locals_to_gitignore(project_dir):
    if not (ignore_path := (project_dir / ".gitignore")).exists():
        ignore_lines = []
    else:
        ignore_lines = ignore_path.read_text().splitlines(keepends=False)
    updated = False
    if LOCAL_CONF_NAME not in ignore_lines:
        _LOG.debug("Add %s to .gitignore", LOCAL_CONF_NAME)
        updated = True
        ignore_lines.append(LOCAL_CONF_NAME)
    if LOCAL_ENV_NAME not in ignore_lines:
        _LOG.debug("Add %s to .gitignore", LOCAL_ENV_NAME)
        updated = True
        ignore_lines.append(LOCAL_ENV_NAME)
    if updated:
        ignore_path.write_text("\n".join(ignore_lines))
