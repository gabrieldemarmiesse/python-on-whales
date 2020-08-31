from typing import List, Optional

from typeguard import typechecked

from .utils import run
from .volume import VolumeDefinition


class ContainerCLI:
    def __init__(self, docker_cmd: List[str]):
        self.docker_cmd = docker_cmd

    def _make_cli_cmd(self) -> List[str]:
        return self.docker_cmd + ["container"]

    @typechecked
    def run(
        self,
        image: str,
        command: Optional[List[str]] = None,
        *,
        remove: bool = False,
        cpus: Optional[float] = None,
        gpus: Optional[str] = None,
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

        if gpus is not None:
            full_cmd += ["--gpus", gpus]

        full_cmd.append(image)
        if command is not None:
            full_cmd += command
        return run(full_cmd)


class Container:
    def __init__(self, container_id: str):
        self.id = container_id
