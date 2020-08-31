import subprocess
from pathlib import Path
from typing import List, Union


class DockerException(Exception):
    def __init__(self, completed_process: subprocess.CompletedProcess):
        error_msg = (
            f"The docker command returned with code {completed_process.returncode}\n"
            f"The content of stderr is '{completed_process.stderr.decode()}'\n"
            f"The content of stdout is '{completed_process.stdout.decode()}'"
        )
        super().__init__(error_msg)


def run(
    args: List[str], capture_stdout: bool = True, capture_stderr: bool = True
) -> str:
    if capture_stdout:
        stdout_dest = subprocess.PIPE
    else:
        stdout_dest = None
    if capture_stderr:
        stderr_dest = subprocess.PIPE
    else:
        stderr_dest = None
    completed_process = subprocess.run(args, stdout=stdout_dest, stderr=stderr_dest)

    if completed_process.returncode != 0:
        raise DockerException(completed_process)
    stdout = completed_process.stdout.decode()
    if len(stdout) != 0 and stdout[-1] == "\n":
        stdout = stdout[:-1]
    return stdout


ValidPath = Union[str, Path]
