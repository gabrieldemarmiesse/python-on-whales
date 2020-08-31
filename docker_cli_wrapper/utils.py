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


def run(args: List[str], stream_output: bool = False) -> str:
    if stream_output:
        raise NotImplementedError()
    completed_process = subprocess.run(args, capture_output=True)
    if completed_process.returncode != 0:
        raise DockerException(completed_process)
    stdout = completed_process.stdout.decode()
    if len(stdout) != 0 and stdout[-1] == "\n":
        stdout = stdout[:-1]
    return stdout


ValidPath = Union[str, Path]
