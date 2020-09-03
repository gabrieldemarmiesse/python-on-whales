import inspect
from datetime import timedelta
from typing import Iterator, List, Optional, Tuple, Union

from typeguard import typechecked

from docker_cli_wrapper.utils import ValidPath, run, to_list

from .image import Image
from .volume import VolumeDefinition


class Container:
    def __init__(self, container_id: str):
        self.id = container_id

    def __eq__(self, other):
        return self.id == other.id

    def __str__(self):
        return self.id


ContainerPath = Tuple[Union[Container, str], ValidPath]
ValidContainer = Union[Container, str]


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

    @typechecked
    def logs(self, container: Union[Container, str]) -> str:
        full_cmd = self._make_cli_cmd() + ["logs"]

        return run(full_cmd + [str(container)])

    @typechecked
    def cp(
        self,
        source: Union[bytes, Iterator[bytes], ValidPath, ContainerPath],
        destination: Union[None, ValidPath, ContainerPath],
    ):
        # TODO: tests and handling bytes streams.
        full_cmd = self._make_cli_cmd() + ["cp"]

        if isinstance(source, bytes) or inspect.isgenerator(source):
            source = "-"
        elif isinstance(source, tuple):
            source = f"{str(source[0])}:{source[1]}"
        else:
            source = str(source)

        if destination is None:
            destination = "-"
        elif isinstance(destination, tuple):
            destination = f"{str(destination[0])}:{destination[1]}"
        else:
            destination = str(destination)

        run(full_cmd + [source, destination])

    @typechecked
    def kill(
        self,
        containers: Union[ValidContainer, List[ValidContainer]],
        signal: str = None,
    ):
        full_cmd = self._make_cli_cmd() + ["kill"]

        if signal is not None:
            full_cmd += ["--signal", signal]

        for container in to_list(containers):
            full_cmd.append(str(container))

        run(full_cmd)

    @typechecked
    def stop(
        self,
        containers: Union[ValidContainer, List[ValidContainer]],
        time: Union[int, timedelta] = None,
    ):
        full_cmd = self._make_cli_cmd() + ["stop"]
        if isinstance(time, timedelta):
            time = time.total_seconds()

        if time is not None:
            full_cmd += ["--time", str(time)]

        for container in to_list(containers):
            full_cmd.append(str(container))

        run(full_cmd)

    @typechecked
    def commit(
        self,
        container: ValidContainer,
        tag: Optional[str] = None,
        author: Optional[str] = None,
        message: Optional[str] = None,
        pause: bool = True,
    ):
        full_cmd = self._make_cli_cmd() + ["commit"]

        if author is not None:
            full_cmd += ["--author", author]

        if message is not None:
            full_cmd += ["--message", message]

        full_cmd += ["--pause", str(pause).lower()]

        full_cmd.append(str(container))
        if tag is not None:
            full_cmd.append(tag)

        return Image(self.docker_cmd, run(full_cmd), is_id=True)
