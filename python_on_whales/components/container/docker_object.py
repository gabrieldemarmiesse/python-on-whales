from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

import pydantic

import python_on_whales.components
from python_on_whales.client_config import ClientConfig, ReloadableObjectFromJson
from python_on_whales.components.container.cli_wrapper import ContainerCLI
from python_on_whales.components.container.models import (
    ContainerConfig,
    ContainerGraphDriver,
    ContainerHostConfig,
    ContainerInspectResult,
    ContainerState,
    Mount,
    NetworkSettings,
)
from python_on_whales.utils import ValidPath, removeprefix, run


class Container(ReloadableObjectFromJson):
    def __init__(
        self, client_config: ClientConfig, reference: str, is_immutable_id=False
    ):
        super().__init__(client_config, "id", reference, is_immutable_id)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        autoremove = self.host_config.auto_remove
        if self.state.running:
            self.stop()
        if not autoremove:
            self.remove(volumes=True)

    def _fetch_inspect_result_json(self, reference):
        return run(self.docker_cmd + ["container", "inspect", reference])

    def _parse_json_object(self, json_object: Dict[str, Any]):
        return ContainerInspectResult.parse_obj(json_object)

    def _get_inspect_result(self) -> ContainerInspectResult:
        """Only there to allow tools to know the return type"""
        return super()._get_inspect_result()

    # ----------------------------------------------------------------
    # attributes taken from the json inspect result
    @property
    def id(self) -> str:
        return self._get_immutable_id()

    @property
    def created(self) -> datetime:
        return self._get_inspect_result().created

    @property
    def path(self) -> str:
        return self._get_inspect_result().path

    @property
    def args(self) -> List[str]:
        return self._get_inspect_result().args

    @property
    def state(self) -> ContainerState:
        return self._get_inspect_result().state

    @property
    def image(self) -> str:
        return self._get_inspect_result().image

    @property
    def resolv_conf_path(self) -> str:
        return self._get_inspect_result().resolv_conf_path

    @property
    def hostname_path(self) -> Path:
        return self._get_inspect_result().hostname_path

    @property
    def hosts_path(self) -> Path:
        return self._get_inspect_result().hosts_path

    @property
    def log_path(self) -> Path:
        return self._get_inspect_result().log_path

    @property
    def node(self) -> Any:
        return self._get_inspect_result().node

    @property
    def name(self) -> str:
        return removeprefix(self._get_inspect_result().name, "/")

    @property
    def restart_count(self) -> int:
        return self._get_inspect_result().restart_count

    @property
    def driver(self) -> str:
        return self._get_inspect_result().driver

    @property
    def platform(self) -> str:
        return self._get_inspect_result().platform

    @property
    def mount_label(self) -> str:
        return self._get_inspect_result().mount_label

    @property
    def process_label(self) -> str:
        return self._get_inspect_result().process_label

    @property
    def app_armor_profile(self) -> str:
        return self._get_inspect_result().app_armor_profile

    @property
    def exec_ids(self) -> Optional[List[str]]:
        return self._get_inspect_result().exec_ids

    @property
    def host_config(self) -> ContainerHostConfig:
        return self._get_inspect_result().host_config

    @property
    def graph_driver(self) -> ContainerGraphDriver:
        return self._get_inspect_result().graph_driver

    @property
    def size_rw(self) -> Optional[int]:
        return self._get_inspect_result().size_rw

    @property
    def size_root_fs(self) -> Optional[int]:
        return self._get_inspect_result().size_root_fs

    @property
    def mounts(self) -> List[Mount]:
        return self._get_inspect_result().mounts

    @property
    def config(self) -> ContainerConfig:
        return self._get_inspect_result().config

    @property
    def network_settings(self) -> NetworkSettings:
        return self._get_inspect_result().network_settings

    # --------------------------------------------------------------------
    # public methods

    def commit(
        self,
        tag: Optional[str] = None,
        author: Optional[str] = None,
        message: Optional[str] = None,
        pause: bool = True,
    ) -> python_on_whales.components.image.docker_object.Image:
        """Create a new image from the container's changes.

        Alias: `docker.commit(...)`

        See the [`docker.container.commit`](../sub-commands/container.md) command for
        information about the arguments.
        """
        return ContainerCLI(self.client_config).commit(
            self, tag, author, message, pause
        )

    def copy_from(self, container_path: ValidPath, local_path: ValidPath):
        return ContainerCLI(self.client_config).copy((self, container_path), local_path)

    def copy_to(self, local_path: ValidPath, container_path: ValidPath):
        return ContainerCLI(self.client_config).copy(local_path, (self, container_path))

    def diff(self) -> Dict[str, str]:
        """Returns the diff of this container filesystem.

        See the [`docker.container.diff`](../sub-commands/container.md) command for
        information about the arguments.
        """
        return ContainerCLI(self.client_config).diff(self)

    def execute(self, command: Union[str, List[str]], detach: bool = False):
        """Execute a command in this container

        See the [`docker.container.execute`](../sub-commands/container.md#execute)
        command for information about the arguments.
        """
        return ContainerCLI(self.client_config).execute(self, command, detach)

    def export(self, output: ValidPath) -> None:
        """Export this container filesystem.

        See the [`docker.container.export`](../sub-commands/container.md) command for
        information about the arguments.
        """
        return ContainerCLI(self.client_config).export(self, output)

    def kill(self, signal: str = None):
        """Kill this container

        See the [`docker.container.kill`](../sub-commands/container.md#kill) command for
        information about the arguments.
        """
        return ContainerCLI(self.client_config).kill(self, signal)

    def logs(
        self,
        details: bool = False,
        since: Union[None, datetime, timedelta] = None,
        tail: Optional[int] = None,
        timestamps: bool = False,
        until: Union[None, datetime, timedelta] = None,
    ) -> str:
        """Returns the logs of the container

        See the [`docker.container.logs`](../sub-commands/container.md#logs) command for
        information about the arguments.
        """
        return ContainerCLI(self.client_config).logs(
            self, details, since, tail, timestamps, until
        )

    def pause(self) -> None:
        """Pause this container.

        See the [`docker.container.pause`](../sub-commands/container.md#pause) command for
        information about the arguments.
        """
        return ContainerCLI(self.client_config).pause(self)

    def unpause(self) -> None:
        """Unpause the container

        See the [`docker.container.unpause`](../sub-commands/container.md#unpause) command for
        information about the arguments.
        """
        return ContainerCLI(self.client_config).unpause(self)

    def rename(self, new_name: str) -> None:
        """Rename this container

        See the [`docker.container.rename`](../sub-commands/container.md#rename) command for
        information about the arguments.
        """
        return ContainerCLI(self.client_config).rename(self, new_name)

    def restart(self, time: Optional[Union[int, timedelta]] = None) -> None:
        """Restarts this container.

        See the [`docker.container.restart`](../sub-commands/container.md#restart) command for
        information about the arguments.
        """
        return ContainerCLI(self.client_config).restart(self, time)

    def remove(self, force: bool = False, volumes: bool = False) -> None:
        """Remove this container.

        See the [`docker.container.remove`](../sub-commands/container.md#remove) command for
        information about the arguments.
        """
        return ContainerCLI(self.client_config).remove(self, force, volumes)

    def start(
        self, attach: bool = False, stream: bool = False
    ) -> Union[None, str, Iterable[Tuple[str, bytes]]]:
        """Starts this container.

        See the [`docker.container.start`](../sub-commands/container.md#start) command for
        information about the arguments.
        """
        return ContainerCLI(self.client_config).start(self, attach, stream)

    def stop(self, time: Union[int, timedelta] = None) -> None:
        """Stops this container.

        See the [`docker.container.stop`](../sub-commands/container.md#stop) command for
        information about the arguments.
        """
        return ContainerCLI(self.client_config).stop(self, time)


class ContainerStats:
    def __init__(self, json_dict: Dict[str, Any]):
        """Takes a json_dict with container stats from the CLI and
        parses it.
        """
        self.block_read: int = pydantic.parse_obj_as(
            pydantic.ByteSize, json_dict["BlockIO"].split("/")[0]
        )
        self.block_write: int = pydantic.parse_obj_as(
            pydantic.ByteSize, json_dict["BlockIO"].split("/")[1]
        )
        self.cpu_percentage: float = float(json_dict["CPUPerc"][:-1])
        self.container: str = json_dict["Container"]
        self.container_id: str = json_dict["ID"]
        self.memory_percentage: float = float(json_dict["MemPerc"][:-1])
        self.memory_used: int = pydantic.parse_obj_as(
            pydantic.ByteSize, json_dict["MemUsage"].split("/")[0]
        )
        self.memory_limit: int = pydantic.parse_obj_as(
            pydantic.ByteSize, json_dict["MemUsage"].split("/")[1]
        )
        self.container_name: str = json_dict["Name"]
        self.net_upload: int = pydantic.parse_obj_as(
            pydantic.ByteSize, json_dict["NetIO"].split("/")[0]
        )
        self.net_download: int = pydantic.parse_obj_as(
            pydantic.ByteSize, json_dict["NetIO"].split("/")[1]
        )

    def __repr__(self):
        attr = ", ".join(f"{key}={value}" for key, value in self.__dict__.items())
        return f"<{self.__class__} object, attributes are {attr}>"


ValidContainer = Union[Container, str]
