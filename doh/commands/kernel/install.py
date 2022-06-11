"""Based on original implementation ..."""

from typing import List

import platform
import sys

from ...config import Context
from .kernelspec import (
    InterruptMode,
    Kernelspec,
    ensure_kernelspec_store_exists,
    install_kernelspec,
    kernelspec_dir,
    user_kernelspec_store,
)

JUPYTER_CONNECTION_FILE_TEMPLATE = "{connection_file}"


def python_argv(system_type: str) -> List[str]:
    """Return proper command-line vector for python interpreter"""
    if system_type == "Linux" or system_type == "Darwin":
        argv = [sys.executable, "-m", "doh"]
    elif system_type == "Windows":
        argv = ["python", "-m", "doh"]
    else:
        raise ValueError(f"unknown system type: {system_type}")
    return argv


def generate_kernelspec_argv(project_root: str, system_type: str) -> List[str]:
    args = [
        "kernel-run",
        project_root,
        JUPYTER_CONNECTION_FILE_TEMPLATE,
    ]
    return python_argv(system_type) + args


def install(context: Context, lang: str) -> int:
    system_type = platform.system()
    store_path = user_kernelspec_store(system_type)
    ensure_kernelspec_store_exists(store_path)

    argv = generate_kernelspec_argv(str(context.project_dir), system_type)
    kernelspec = Kernelspec(
        argv, context.project_name, lang, interrupt_mode=InterruptMode.message
    )

    kernel_id = context.project_name
    location = kernelspec_dir(store_path, kernel_id)
    install_kernelspec(location, kernelspec)

    return 0
