import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pydantic

from python_on_whales.download_binaries import download_buildx


def title_if_necessary(string: str):
    if string.isupper():
        return string
    else:
        return string.title()


def to_docker_camel(string):
    return "".join(title_if_necessary(x) for x in string.split("_"))


class DockerCamelModel(pydantic.BaseModel):
    class Config:
        alias_generator = to_docker_camel
        allow_population_by_field_name = True


class DockerException(Exception):
    def __init__(
        self,
        command_launched: List[str],
        return_code: int,
        stdout: Optional[bytes] = None,
        stderr: Optional[bytes] = None,
    ):
        command_launched_str = " ".join(command_launched)
        error_msg = (
            f"The docker command executed was `{command_launched_str}`.\n"
            f"It returned with code {return_code}\n"
        )
        if stdout is not None:
            error_msg += f"The content of stdout is '{stdout.decode()}'\n"
        else:
            error_msg += (
                "The content of stdout can be found above the "
                "stacktrace (it wasn't captured).\n"
            )
        if stderr is not None:
            error_msg += f"The content of stderr is '{stderr.decode()}'\n"
        else:
            error_msg += (
                "The content of stderr can be found above the "
                "stacktrace (it wasn't captured)."
            )
        super().__init__(error_msg)


def run(
    args: List[Any],
    capture_stdout: bool = True,
    capture_stderr: bool = True,
    input: bytes = None,
) -> Optional[str]:
    args = [str(x) for x in args]
    if args[1] == "buildx":
        install_buildx_if_needed(args[0])
        env = {"DOCKER_CLI_EXPERIMENTAL": "enabled"}
    else:
        env = None
    if capture_stdout:
        stdout_dest = subprocess.PIPE
    else:
        stdout_dest = None
    if capture_stderr:
        stderr_dest = subprocess.PIPE
    else:
        stderr_dest = None
    completed_process = subprocess.run(
        args, input=input, stdout=stdout_dest, stderr=stderr_dest, env=env
    )

    if completed_process.returncode != 0:
        raise DockerException(
            args,
            completed_process.returncode,
            completed_process.stdout,
            completed_process.stderr,
        )
    if completed_process.stdout is None:
        return
    stdout = completed_process.stdout.decode()
    if len(stdout) != 0 and stdout[-1] == "\n":
        stdout = stdout[:-1]
    return stdout


ValidPath = Union[str, Path]


def to_list(x) -> list:
    if isinstance(x, list):
        return x
    else:
        return [x]


# backport of https://docs.python.org/3.9/library/stdtypes.html#str.removesuffix
def removesuffix(string: str, suffix: str) -> str:
    if string.endswith(suffix):
        return string[: -len(suffix)]
    else:
        return string


def removeprefix(string: str, prefix: str) -> str:
    if string.startswith(prefix):
        return string[len(prefix) :]
    else:
        return string


def install_buildx_if_needed(docker_binary: str):
    completed_process = subprocess.run(
        [docker_binary, "buildx"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={"DOCKER_CLI_EXPERIMENTAL": "enabled"},
    )
    if completed_process.returncode == 0:
        return

    stderr = completed_process.stderr.decode()
    if "is not a docker command" in stderr:
        download_buildx()
    else:
        raise RuntimeError(
            f"It seems buildx is not properly installed. When running "
            f"'docker buildx', here is the result:\n"
            f"{stderr}"
        )
