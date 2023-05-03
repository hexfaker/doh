from typing import IO, List, Tuple

import json
import os
import shlex
import subprocess
from pathlib import Path
from tempfile import NamedTemporaryFile

from doh.config import Context
from doh.docker import build_image, docker_run_args_from_project, run_docker_run

KERNEL_CONN_SPEC_CONTAINER_PATH = "/kernel-connection-spec.json"
IPYKERNEL_CMD = (
    f"/usr/bin/env python -m ipykernel -f {KERNEL_CONN_SPEC_CONTAINER_PATH}"
)


def patch_connection_ip(
    connection_file: Path, file: IO[str], ip: str = "0.0.0.0"
) -> None:
    """Set/update ip field in connection file"""
    connection = json.loads(connection_file.read_text())
    connection["ip"] = ip
    file.write(json.dumps(connection))
    file.flush()


def docker_run_args_for_kernel(
    orig_conn_spec_path: Path, patched_conn_spec_path: str
) -> List[str]:
    ip, ports = parse_conn_spec(orig_conn_spec_path)

    args: List[str] = sum((["--publish", f"{ip}:{p}:{p}"] for p in ports), [])
    args += [
        "--volume",
        f"{patched_conn_spec_path}:{KERNEL_CONN_SPEC_CONTAINER_PATH}",
    ]
    return args


def parse_conn_spec(path: Path) -> Tuple[str, List[int]]:
    conn_spec = json.loads(path.read_text())
    return conn_spec.get("ip", "127.0.0.1"), [
        port
        for k, port in conn_spec.items()
        if "port" in k and k != "transport"
    ]


def run_kernel(
    project: Context, kernel_conn_spec_path: Path, build: bool
) -> None:
    os.chdir(project.project_dir)
    if build:
        build_image(project.config, project)

    if project.config.before_command:
        subprocess.run(shlex.split(project.config.before_command), check=True)

    run_args = docker_run_args_from_project(project, request_tty=False)

    if project.config.after_command:
        subprocess.run(shlex.split(project.config.after_command), check=True)

    with NamedTemporaryFile(
        "w",
        prefix="doh-kernel_",
        suffix=".json",
        dir=kernel_conn_spec_path.parent,
    ) as patched_conn_spec:
        patch_connection_ip(kernel_conn_spec_path, patched_conn_spec)
        run_args += docker_run_args_for_kernel(
            kernel_conn_spec_path, patched_conn_spec.name
        )
        run_docker_run(run_args, project.image_name, IPYKERNEL_CMD)
