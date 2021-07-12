from datetime import datetime
from typing import Any, Dict, List

import pydantic

from python_on_whales.utils import DockerCamelModel, all_fields_optional


@all_fields_optional
class ObjectVersion(DockerCamelModel):
    index: int


@all_fields_optional
class NamedResourceSpec(DockerCamelModel):
    kind: str
    value: str


@all_fields_optional
class DiscreteResourceSpec(DockerCamelModel):
    kind: str
    value: int


@all_fields_optional
class AssignedGenericResources(DockerCamelModel):
    named_resource_spec: NamedResourceSpec
    discrete_resource_spec: DiscreteResourceSpec


@all_fields_optional
class ContainerStatus(DockerCamelModel):
    container_id: str = pydantic.Field(alias="ContainerID")
    pid: int = pydantic.Field(alias="PID")
    exit_code: int


@all_fields_optional
class TaskStatus(DockerCamelModel):
    timestamp: datetime
    state: str
    message: str
    err: str
    container_status: ContainerStatus


@all_fields_optional
class LogDriver(DockerCamelModel):
    name: str
    options: Dict[str, str]


@all_fields_optional
class NetworkAttachmentConfig(DockerCamelModel):
    target: str
    aliases: List[str]
    driver_opts: Dict[str, str]


@all_fields_optional
class Platform(DockerCamelModel):
    architecture: str
    os: str = pydantic.Field(alias="OS")


@all_fields_optional
class Spread(DockerCamelModel):
    spread_descriptor: str


@all_fields_optional
class Placement(DockerCamelModel):
    constraints: List[str]
    preferences: List[Spread]
    max_replicas: int
    platforms: List[Platform]


@all_fields_optional
class RestartPolicy(DockerCamelModel):
    condition: str
    delay: int
    max_attempts: int
    window: int


@all_fields_optional
class PluginPrivilege(DockerCamelModel):
    name: str
    description: str
    value: List[str]


@all_fields_optional
class PluginSpec(DockerCamelModel):
    name: str
    remote: str
    disabled: bool
    plugin_privilege: List[PluginPrivilege]


@all_fields_optional
class ContainerSpec(DockerCamelModel):
    image: str
    labels: Dict[str, str]
    command: List[str]
    args: List[str]
    hostname: str
    env: List[str]
    dir: str
    user: str
    groups: List[str]
    privileges: Any
    tty: bool = pydantic.Field(alias="TTY")
    open_stdin: bool
    read_only: bool
    mounts: List[Any]
    stop_signal: str
    stop_grace_period: int
    health_check: Any
    hosts: List[str]
    dns_config: Any
    secrets: List[Any]
    configs: List[Any]
    isolation: str
    init: bool
    sysctls: Any


@all_fields_optional
class NetworkAttachmentSpec(DockerCamelModel):
    container_id: str = pydantic.Field(alias="ContainerID")


@all_fields_optional
class ResourceObject(DockerCamelModel):
    nano_cpus: int = pydantic.Field(alias="NanoCPUs")
    memory_bytes: int
    generic_resources: List[AssignedGenericResources]


@all_fields_optional
class Resources(DockerCamelModel):
    limits: ResourceObject
    reservation: ResourceObject


@all_fields_optional
class TaskSpec(DockerCamelModel):
    # TODO: set types for Any
    plugin_spec: PluginSpec
    container_spec: ContainerSpec
    network_attachment_spec: NetworkAttachmentSpec
    resources: Resources
    restart_policy: Any
    placement: Placement
    force_update: int
    runtime: str
    networks: List[NetworkAttachmentConfig]
    log_driver: LogDriver


@all_fields_optional
class TaskInspectResult(DockerCamelModel):
    id: str = pydantic.Field(alias="ID")
    version: ObjectVersion
    created_at: datetime
    updated_at: datetime
    name: str
    labels: Dict[str, str]
    spec: TaskSpec
    service_id: str = pydantic.Field(alias="ServiceID")
    slot: int
    node_id: str = pydantic.Field(alias="NodeID")
    assigned_generic_resources: List[AssignedGenericResources]
    status: TaskStatus
    desired_state: str
