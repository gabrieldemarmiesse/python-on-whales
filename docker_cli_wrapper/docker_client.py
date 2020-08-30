import subprocess
from pathlib import Path
from typing import List, Optional, Tuple, Union

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
    if len(stdout) != 0 and stdout[-1] == "\n":
        stdout = stdout[:-1]
    return stdout


ValidPath = Union[str, Path]
VolumeDefinition = Union[Tuple[ValidPath, ValidPath, str], Tuple[ValidPath, ValidPath]]


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

        self.volume = VolumeCLI(self)
        self.image = ImageCLI(self)

    def _make_cli_cmd(self) -> List[str]:
        result = ["docker"]

        if self.config is not None:
            result += ["--config", self.config]

        return result

    @typechecked
    def run(
        self,
        image: str,
        command: Optional[List[str]] = None,
        *,
        remove: bool = False,
        cpus: Optional[float] = None,
        runtime: Optional[str] = None,
        volumes: Optional[List[VolumeDefinition]] = [],
    ) -> str:
        full_cmd = self._make_cli_cmd() + ["run"]

        if remove:
            full_cmd.append("--rm")

        if cpus is not None:
            full_cmd += ["--cpus", str(cpus)]
        if runtime is not None:
            full_cmd += ["--runtime", runtime]
        for volume_definition in volumes:
            full_cmd += ["--volume", ":".join(volume_definition)]

        full_cmd.append(image)
        if command is not None:
            full_cmd += command
        return run(full_cmd)


class VolumeCLI:
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
    def remove(self, x: Union[str, List[str]]) -> List[str]:
        full_cmd = self._make_cli_cmd() + ["remove"]
        if isinstance(x, str):
            full_cmd.append(x)
        if isinstance(x, list):
            full_cmd += x

        return run(full_cmd).split("\n")


class ImageCLI:
    def __init__(self, docker_client: DockerClient):
        self.docker_client = docker_client

    def _make_cli_cmd(self) -> List[str]:
        return self.docker_client._make_cli_cmd() + ["image"]

    def pull(self, image_name, quiet=False):
        if not quiet:
            raise NotImplementedError
        full_cmd = self._make_cli_cmd() + ["pull"]

        if quiet:
            full_cmd.append("--quiet")

        full_cmd.append(image_name)
        run(full_cmd)

    @typechecked
    def remove(self, x: Union[str, List[str]]) -> List[str]:
        full_cmd = self._make_cli_cmd() + ["remove"]
        if isinstance(x, str):
            full_cmd.append(x)
        if isinstance(x, list):
            full_cmd += x

        return run(full_cmd).split("\n")


class Image:
    def __init__(self, sha256: str):
        self.sha256 = sha256


class Container:
    def __init__(self, container_id):
        self.id = container_id
