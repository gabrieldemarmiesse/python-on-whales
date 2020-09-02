from typing import List, Optional, Union

from typeguard import typechecked

from docker_cli_wrapper.utils import run, to_list

from .volume import VolumeDefinition


class Container:
    def __init__(self, container_id: str):
        self.id = container_id

    def __eq__(self, other):
        return self.id == other.id

    def __str__(self):
        return self.id


class ContainerCLI:
    def __init__(self, docker_cmd: List[str]):
        self.docker_cmd = docker_cmd

    def _make_cli_cmd(self) -> List[str]:
        return self.docker_cmd + ["container"]

    @typechecked
    def list(self, all: bool = False) -> List[Container]:
        full_cmd = self._make_cli_cmd() + ["list", "-q", "--no-trunc"]
        if all:
            full_cmd.append("--all")

        return [Container(x) for x in run(full_cmd).splitlines()]

    @typechecked
    def remove(
        self,
        containers: Union[Container, str, List[Union[Container, str]]],
        force: bool = False,
        volumes=False,
    ) -> List[str]:
        full_cmd = self._make_cli_cmd() + ["rm"]

        if force:
            full_cmd.append("--force")
        if volumes:
            full_cmd.append("--volumes")

        for container in to_list(containers):
            full_cmd.append(str(container))

        return run(full_cmd).splitlines()

    @typechecked
    def run(
        self,
        image: str,
        command: Optional[List[str]] = None,
        *,
        detach: bool = False,
        remove: bool = False,
        cpus: Optional[float] = None,
        gpus: Optional[str] = None,
        runtime: Optional[str] = None,
        volumes: Optional[List[VolumeDefinition]] = [],
    ) -> Union[Container, str]:
        full_cmd = self._make_cli_cmd() + ["run"]

        if remove:
            full_cmd.append("--rm")
        if detach:
            full_cmd.append("--detach")

        if cpus is not None:
            full_cmd += ["--cpus", str(cpus)]
        if runtime is not None:
            full_cmd += ["--runtime", runtime]
        for volume_definition in volumes:
            volume_definition = tuple(str(x) for x in volume_definition)
            full_cmd += ["--volume", ":".join(volume_definition)]

        if gpus is not None:
            full_cmd += ["--gpus", gpus]

        full_cmd.append(image)
        if command is not None:
            full_cmd += command

        if detach:
            return Container(run(full_cmd))
        else:
            return run(full_cmd)
