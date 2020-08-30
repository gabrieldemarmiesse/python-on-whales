from pathlib import Path
from typing import Union, Optional, List
import subprocess
from typeguard import typechecked


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
    if stdout[-1] == "\n":
        stdout = stdout[:-1]
    return stdout


ValidPath = Union[str, Path]


class DockerClient:
    def __init__(
        self,
        config: Optional[ValidPath] = None,
        context: Optional[str] = None,
        debug: Optional[bool] = None,
        host: Optional[str] = None,
        log_level: Optional[str] = None,
        tls: Optional[bool] = None,
        tlscacert: Optional[ValidPath] = None,
        tlscert: Optional[ValidPath] = None,
        tlskey: Optional[ValidPath] = None,
        tlsverify: Optional[bool] = None,
        version: bool = False,
    ):
        self.config = config
        self.context = context
        self.debug = debug
        self.host = host
        self.log_level = log_level
        self.tls = tls
        self.tlscacert = tlscacert
        self.tlscert = tlscert
        self.tlskey = tlskey
        self.tlsverify = tlsverify
        self.version = version

        self.volume = VolumeCli(self)

    def _make_cli_cmd(self) -> List[str]:
        result = ["docker"]

        if self.config is not None:
            result += ["--config", self.config]

        return result

    def run(self, image: str, command: Optional[List[str]] = None) -> str:
        full_cmd = self._make_cli_cmd() + ["run", image]
        if command is not None:
            full_cmd += command
        return run(full_cmd)


class VolumeCli:
    def __init__(self, docker_client: DockerClient):
        self.docker_client = docker_client

    def _make_cli_cmd(self) -> List[str]:
        return self.docker_client._make_cli_cmd() + ["volume"]

    def create(self, volume_name: Optional[str] = None) -> str:
        full_cmd = self._make_cli_cmd() + ["create"]

        if volume_name is not None:
            full_cmd += [volume_name]

        return run(full_cmd)

    @typechecked
    def remove(self, volumes_names: List[str]) -> str:
        full_cmd = self._make_cli_cmd() + ["remove"]
        full_cmd += volumes_names

        return run(full_cmd)
