import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Union


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
    args: List[str],
    capture_stdout: bool = True,
    capture_stderr: bool = True,
    env: Optional[Dict[str, str]] = None,
) -> Optional[str]:
    if capture_stdout:
        stdout_dest = subprocess.PIPE
    else:
        stdout_dest = None
    if capture_stderr:
        stderr_dest = subprocess.PIPE
    else:
        stderr_dest = None
    completed_process = subprocess.run(
        args, stdout=stdout_dest, stderr=stderr_dest, env=env
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
