import inspect
import json
from datetime import datetime, timedelta
from typing import Any, Dict, Iterator, List, Optional, Tuple, Union

from docker_cli_wrapper.client_config import (
    ClientConfig,
    DockerCLICaller,
    ReloadableObjectFromJson,
)
from docker_cli_wrapper.utils import (
    DockerCamelModel,
    ValidPath,
    removeprefix,
    run,
    to_list,
)

from .image import Image
from .volume import VolumeDefinition


class ContainerState(DockerCamelModel):
    status: str
    running: bool
    paused: bool
    restarting: bool
    OOM_killed: bool
    dead: bool
    pid: int
    exit_code: int
    error: str
    started_at: datetime
    finished_at: datetime


class ContainerInspectResult(DockerCamelModel):
    id: str
    created: datetime
    image: str
    name: str
    state: ContainerState


class Container(ReloadableObjectFromJson):
    def __init__(
        self, client_config: ClientConfig, reference: str, is_immutable_id=False
    ):
        super().__init__(client_config, "id", reference, is_immutable_id)

    def _fetch_inspect_result_json(self, reference):
        return run(self.docker_cmd + ["container", "inspect", reference])

    def _parse_json_object(self, json_object: Dict[str, Any]):
        return ContainerInspectResult.parse_obj(json_object)

    @property
    def id(self):
        return self._get_immutable_id()

    @property
    def name(self):
        return removeprefix(self._get_inspect_result().name, "/")

    @property
    def state(self) -> ContainerState:
        return self._get_inspect_result().state

    @property
    def image(self) -> Image:
        return Image(self.client_config, ...)


ContainerPath = Tuple[Union[Container, str], ValidPath]
ValidContainer = Union[Container, str]


class ContainerCLI(DockerCLICaller):
    def list(self, all: bool = False) -> List[Container]:
        full_cmd = self.docker_cmd
        full_cmd += ["container", "list", "-q", "--no-trunc"]
        if all:
            full_cmd.append("--all")

        return [Container(self.client_config, x) for x in run(full_cmd).splitlines()]

    def remove(
        self,
        containers: Union[Container, str, List[Union[Container, str]]],
        force: bool = False,
        volumes=False,
    ) -> List[str]:
        full_cmd = self.docker_cmd + ["container", "rm"]

        if force:
            full_cmd.append("--force")
        if volumes:
            full_cmd.append("--volumes")

        for container in to_list(containers):
            full_cmd.append(str(container))

        return run(full_cmd).splitlines()

    def run(
        self,
        image: str,
        command: Optional[List[str]] = None,
        *,
        name: Optional[str] = None,
        detach: bool = False,
        remove: bool = False,
        cpus: Optional[float] = None,
        gpus: Optional[str] = None,
        runtime: Optional[str] = None,
        volumes: Optional[List[VolumeDefinition]] = [],
    ) -> Union[Container, str]:
        full_cmd = self.docker_cmd + ["container", "run"]

        if remove:
            full_cmd.append("--rm")
        if detach:
            full_cmd.append("--detach")
        if name is not None:
            full_cmd += ["--name", name]

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
            return Container(self.client_config, run(full_cmd))
        else:
            return run(full_cmd)

    def logs(self, container: Union[Container, str]) -> str:
        full_cmd = self.docker_cmd + ["container", "logs"]

        return run(full_cmd + [str(container)])

    def cp(
        self,
        source: Union[bytes, Iterator[bytes], ValidPath, ContainerPath],
        destination: Union[None, ValidPath, ContainerPath],
    ):
        # TODO: tests and handling bytes streams.
        full_cmd = self.docker_cmd + ["container", "cp"]

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

    def kill(
        self,
        containers: Union[ValidContainer, List[ValidContainer]],
        signal: str = None,
    ):
        full_cmd = self.docker_cmd + ["container", "kill"]

        if signal is not None:
            full_cmd += ["--signal", signal]

        for container in to_list(containers):
            full_cmd.append(str(container))

        run(full_cmd)

    def stop(
        self,
        containers: Union[ValidContainer, List[ValidContainer]],
        time: Union[int, timedelta] = None,
    ):
        full_cmd = self.docker_cmd + ["container", "stop"]
        if isinstance(time, timedelta):
            time = time.total_seconds()

        if time is not None:
            full_cmd += ["--time", str(time)]

        for container in to_list(containers):
            full_cmd.append(str(container))

        run(full_cmd)

    def commit(
        self,
        container: ValidContainer,
        tag: Optional[str] = None,
        author: Optional[str] = None,
        message: Optional[str] = None,
        pause: bool = True,
    ):
        full_cmd = self.docker_cmd + ["container", "commit"]

        if author is not None:
            full_cmd += ["--author", author]

        if message is not None:
            full_cmd += ["--message", message]

        full_cmd += ["--pause", str(pause).lower()]

        full_cmd.append(str(container))
        if tag is not None:
            full_cmd.append(tag)

        return Image(self.client_config, run(full_cmd), is_id=True)

    def rename(self, container: ValidContainer, new_name: str) -> None:
        full_cmd = self.docker_cmd + ["container", "rename", str(container), new_name]
        run(full_cmd)

    def restart(
        self,
        containers: Union[ValidContainer, List[ValidContainer]],
        time: Optional[Union[int, timedelta]] = None,
    ):
        full_cmd = self.docker_cmd + ["restart"]

        if time is not None:
            if isinstance(time, timedelta):
                time = time.total_seconds()
            full_cmd += ["--time", str(time)]

        for container in to_list(containers):
            full_cmd.append(str(container))

        run(full_cmd)

    def pause(self, containers: Union[ValidContainer, List[ValidContainer]]):
        full_cmd = self.docker_cmd + ["pause"]
        for container in to_list(containers):
            full_cmd.append(str(container))

        run(full_cmd)

    def port(self, container: ValidContainer, private_port: Union[str, int] = None):
        raise NotImplementedError
