from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import pydantic

import python_on_whales.components.service
from python_on_whales.client_config import (
    ClientConfig,
    DockerCLICaller,
    ReloadableObjectFromJson,
)
from python_on_whales.utils import DockerCamelModel, run


class ObjectVersion(DockerCamelModel):
    index: int


class NamedResourceSpec(DockerCamelModel):
    kind: str
    value: str


class DiscreteResourceSpec(DockerCamelModel):
    kind: str
    value: int


class AssignedGenericResources(DockerCamelModel):
    named_resource_spec: Optional[NamedResourceSpec]
    discrete_resource_spec: Optional[DiscreteResourceSpec]


class ContainerStatus(DockerCamelModel):
    container_id: str = pydantic.Field(alias="ContainerID")
    pid: int = pydantic.Field(alias="PID")
    exit_code: Optional[int]


class TaskStatus(DockerCamelModel):
    timestamp: datetime
    state: str
    message: str
    err: Optional[str]
    container_status: Optional[ContainerStatus]


class LogDriver(DockerCamelModel):
    name: str
    options: Dict[str, str]


class NetworkAttachmentConfig(DockerCamelModel):
    target: str
    aliases: List[str]
    driver_opts: Optional[Dict[str, str]]


class Platform(DockerCamelModel):
    architecture: Optional[str]
    os: Optional[str] = pydantic.Field(alias="OS")


class Spread(DockerCamelModel):
    spread_descriptor: str


class Placement(DockerCamelModel):
    constraints: Optional[List[str]]
    preferences: Optional[List[Spread]]
    max_replicas: Optional[int]
    platforms: Optional[List[Platform]]


class RestartPolicy(DockerCamelModel):
    condition: str
    delay: int
    max_attempts: int
    window: int


class PluginPrivilege(DockerCamelModel):
    name: str
    description: str
    value: List[str]


class PluginSpec(DockerCamelModel):
    name: str
    remote: str
    disabled: bool
    plugin_privilege: List[PluginPrivilege]


class ContainerSpec(DockerCamelModel):
    image: str
    labels: Optional[Dict[str, str]]
    command: Optional[List[str]]
    args: Optional[List[str]]
    hostname: Optional[str]
    env: Optional[List[str]]
    dir: Optional[str]
    user: Optional[str]
    groups: Optional[List[str]]
    privileges: Any
    tty: Optional[bool] = pydantic.Field(alias="TTY")
    open_stdin: Optional[bool]
    read_only: Optional[bool]
    mounts: Optional[List[Any]]
    stop_signal: Optional[str]
    stop_grace_period: Optional[int]
    health_check: Any
    hosts: Optional[List[str]]
    dns_config: Any
    secrets: Optional[List[Any]]
    configs: Optional[List[Any]]
    isolation: Optional[str]
    init: Optional[bool]
    sysctls: Any


class NetworkAttachmentSpec(DockerCamelModel):
    container_id: str = pydantic.Field(alias="ContainerID")


class ResourceObject(DockerCamelModel):
    nano_cpus: Optional[int] = pydantic.Field(alias="NanoCPUs")
    memory_bytes: Optional[int]
    generic_resources: Optional[List[AssignedGenericResources]]


class Resources(DockerCamelModel):
    limits: Optional[ResourceObject]
    reservation: Optional[ResourceObject]


class TaskSpec(DockerCamelModel):
    # TODO: set types for Any
    plugin_spec: Optional[PluginSpec]
    container_spec: Optional[ContainerSpec]
    network_attachment_spec: Optional[NetworkAttachmentSpec]
    resources: Resources
    restart_policy: Any
    placement: Placement
    force_update: Optional[int]
    runtime: Optional[str]
    networks: Optional[List[NetworkAttachmentConfig]]
    log_driver: Optional[LogDriver]


class TaskInspectResult(DockerCamelModel):
    id: str = pydantic.Field(alias="ID")
    version: ObjectVersion
    created_at: datetime
    updated_at: datetime
    name: Optional[str]
    labels: Optional[Dict[str, str]]
    spec: TaskSpec
    service_id: str = pydantic.Field(alias="ServiceID")
    slot: Optional[int]
    node_id: Optional[str] = pydantic.Field(alias="NodeID")
    assigned_generic_resources: Optional[List[AssignedGenericResources]]
    status: TaskStatus
    desired_state: str


class Task(ReloadableObjectFromJson):
    def __init__(
        self, client_config: ClientConfig, reference: str, is_immutable_id=False
    ):
        super().__init__(client_config, "id", reference, is_immutable_id)

    def _fetch_inspect_result_json(self, reference):
        return run(self.docker_cmd + ["inspect", reference])

    def _parse_json_object(self, json_object: Dict[str, Any]) -> TaskInspectResult:
        return TaskInspectResult.parse_obj(json_object)

    def _get_inspect_result(self) -> TaskInspectResult:
        """Only there to allow tools to know the return type"""
        return super()._get_inspect_result()

    @property
    def id(self) -> str:
        return self._get_immutable_id()

    @property
    def version(self) -> ObjectVersion:
        return self._get_inspect_result().version

    @property
    def created_at(self) -> datetime:
        return self._get_inspect_result().created_at

    @property
    def updated_at(self) -> datetime:
        return self._get_inspect_result().updated_at

    @property
    def name(self) -> Optional[str]:
        return self._get_inspect_result().name

    @property
    def labels(self) -> Dict[str, str]:
        return self._get_inspect_result().labels

    @property
    def spec(self) -> TaskSpec:
        return self._get_inspect_result().spec

    @property
    def service_id(self) -> str:
        return self._get_inspect_result().service_id

    @property
    def slot(self) -> Optional[int]:
        return self._get_inspect_result().slot

    @property
    def node_id(self) -> str:
        return self._get_inspect_result().node_id

    @property
    def assigned_generic_resources(self) -> Optional[List[AssignedGenericResources]]:
        return self._get_inspect_result().assigned_generic_resources

    @property
    def status(self) -> TaskStatus:
        return self._get_inspect_result().status

    @property
    def desired_state(self) -> str:
        return self._get_inspect_result().desired_state


class TaskCLI(DockerCLICaller):
    def list(self) -> List[Task]:
        """Returns all tasks in the swarm

        # Returns
            `List[python_on_whales.Task]`
        """
        service_cli = python_on_whales.components.service.ServiceCLI(self.client_config)
        return service_cli.ps(service_cli.list())

    def inspect(self, x: Union[str, List[str]]) -> Union[Task, List[Task]]:
        """Returns a `python_on_whales.Task` object from its ID."""
        if isinstance(x, str):
            return Task(self.client_config, x)
        else:
            return [Task(self.client_config, reference) for reference in x]

    def logs(self):
        """Not Yet implemented"""
        raise NotImplementedError
