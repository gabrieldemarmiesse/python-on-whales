from datetime import datetime
from typing import Any, Dict, List, Optional

import pydantic

from python_on_whales.utils import DockerCamelModel, all_fields_optional


@all_fields_optional
class ObjectVersion(DockerCamelModel):
    index: Optional[int]


@all_fields_optional
class NamedResourceSpec(DockerCamelModel):
    kind: Optional[str]
    value: Optional[str]


@all_fields_optional
class DiscreteResourceSpec(DockerCamelModel):
    kind: Optional[str]
    value: Optional[int]


@all_fields_optional
class AssignedGenericResources(DockerCamelModel):
    named_resource_spec: Optional[NamedResourceSpec]
    discrete_resource_spec: Optional[DiscreteResourceSpec]


@all_fields_optional
class ContainerStatus(DockerCamelModel):
    container_id: Optional[str] = pydantic.Field(None, alias="ContainerID")
    pid: Optional[int] = pydantic.Field(None, alias="PID")
    exit_code: Optional[int]


@all_fields_optional
class TaskStatus(DockerCamelModel):
    timestamp: Optional[datetime]
    state: Optional[str]
    message: Optional[str]
    err: Optional[str]
    container_status: Optional[ContainerStatus]


@all_fields_optional
class LogDriver(DockerCamelModel):
    name: Optional[str]
    options: Optional[Dict[str, str]]


@all_fields_optional
class NetworkAttachmentConfig(DockerCamelModel):
    target: Optional[str]
    aliases: Optional[List[str]]
    driver_opts: Optional[Dict[str, str]]


@all_fields_optional
class Platform(DockerCamelModel):
    architecture: Optional[str]
    os: Optional[str] = pydantic.Field(None, alias="OS")


@all_fields_optional
class Spread(DockerCamelModel):
    spread_descriptor: Optional[str]


@all_fields_optional
class Placement(DockerCamelModel):
    constraints: Optional[List[str]]
    preferences: Optional[List[Spread]]
    max_replicas: Optional[int]
    platforms: Optional[List[Platform]]


@all_fields_optional
class RestartPolicy(DockerCamelModel):
    condition: Optional[str]
    delay: Optional[int]
    max_attempts: Optional[int]
    window: Optional[int]


@all_fields_optional
class PluginPrivilege(DockerCamelModel):
    name: Optional[str]
    description: Optional[str]
    value: Optional[List[str]]


@all_fields_optional
class PluginSpec(DockerCamelModel):
    name: Optional[str]
    remote: Optional[str]
    disabled: Optional[bool]
    plugin_privilege: Optional[List[PluginPrivilege]]


@all_fields_optional
class ContainerSpec(DockerCamelModel):
    image: Optional[str]
    labels: Optional[Dict[str, str]]
    command: Optional[List[str]]
    args: Optional[List[str]]
    hostname: Optional[str]
    env: Optional[List[str]]
    dir: Optional[str]
    user: Optional[str]
    groups: Optional[List[str]]
    privileges: Optional[Any]
    tty: Optional[bool] = pydantic.Field(None, alias="TTY")
    open_stdin: Optional[bool]
    read_only: Optional[bool]
    mounts: Optional[List[Any]]
    stop_signal: Optional[str]
    stop_grace_period: Optional[int]
    health_check: Any = None
    hosts: Optional[List[str]]
    dns_config: Any = None
    secrets: Optional[List[Any]]
    configs: Optional[List[Any]]
    isolation: Optional[str]
    init: Optional[bool]
    sysctls: Optional[Any]


@all_fields_optional
class NetworkAttachmentSpec(DockerCamelModel):
    container_id: Optional[str] = pydantic.Field(None, alias="ContainerID")


@all_fields_optional
class ResourceObject(DockerCamelModel):
    nano_cpus: Optional[int] = pydantic.Field(None, alias="NanoCPUs")
    memory_bytes: Optional[int]
    generic_resources: Optional[List[AssignedGenericResources]]


@all_fields_optional
class Resources(DockerCamelModel):
    limits: Optional[ResourceObject]
    reservation: Optional[ResourceObject]


@all_fields_optional
class TaskSpec(DockerCamelModel):
    # TODO: set types for Any
    plugin_spec: Optional[PluginSpec]
    container_spec: Optional[ContainerSpec]
    network_attachment_spec: Optional[NetworkAttachmentSpec]
    resources: Optional[Resources]
    restart_policy: Any = None
    placement: Optional[Placement]
    force_update: Optional[int]
    runtime: Optional[str]
    networks: Optional[List[NetworkAttachmentConfig]]
    log_driver: Optional[LogDriver]


@all_fields_optional
class TaskInspectResult(DockerCamelModel):
    id: Optional[str] = pydantic.Field(None, alias="ID")
    version: Optional[ObjectVersion]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    name: Optional[str]
    labels: Optional[Dict[str, str]]
    spec: Optional[TaskSpec]
    service_id: Optional[str] = pydantic.Field(None, alias="ServiceID")
    slot: Optional[int]
    node_id: Optional[str] = pydantic.Field(None, alias="NodeID")
    assigned_generic_resources: Optional[List[AssignedGenericResources]]
    status: Optional[TaskStatus]
    desired_state: Optional[str]
