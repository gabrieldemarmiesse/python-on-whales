from datetime import datetime
from typing import Any, Dict, List, Optional

import pydantic

from python_on_whales.utils import DockerCamelModel


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
