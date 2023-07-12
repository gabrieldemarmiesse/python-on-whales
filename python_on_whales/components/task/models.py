from datetime import datetime
from typing import Any, Dict, List, Optional

import pydantic
from typing_extensions import Annotated

from python_on_whales.utils import DockerCamelModel


class ObjectVersion(DockerCamelModel):
    index: Optional[int] = None


class NamedResourceSpec(DockerCamelModel):
    kind: Optional[str] = None
    value: Optional[str] = None


class DiscreteResourceSpec(DockerCamelModel):
    kind: Optional[str] = None
    value: Optional[int] = None


class AssignedGenericResources(DockerCamelModel):
    named_resource_spec: Optional[NamedResourceSpec] = None
    discrete_resource_spec: Optional[DiscreteResourceSpec] = None


class ContainerStatus(DockerCamelModel):
    container_id: Annotated[Optional[str], pydantic.Field(alias="ContainerID")] = None
    pid: Annotated[Optional[int], pydantic.Field(alias="PID")] = None
    exit_code: Optional[int] = None


class TaskStatus(DockerCamelModel):
    timestamp: Optional[datetime] = None
    state: Optional[str] = None
    message: Optional[str] = None
    err: Optional[str] = None
    container_status: Optional[ContainerStatus] = None


class LogDriver(DockerCamelModel):
    name: Optional[str] = None
    options: Optional[Dict[str, str]] = None


class NetworkAttachmentConfig(DockerCamelModel):
    target: Optional[str] = None
    aliases: Optional[List[str]] = None
    driver_opts: Optional[Dict[str, str]] = None


class Platform(DockerCamelModel):
    architecture: Optional[str] = None
    os: Annotated[Optional[str], pydantic.Field(alias="OS")] = None


class Spread(DockerCamelModel):
    spread_descriptor: Optional[str] = None


class Placement(DockerCamelModel):
    constraints: Optional[List[str]] = None
    preferences: Optional[List[Spread]] = None
    max_replicas: Optional[int] = None
    platforms: Optional[List[Platform]] = None


class RestartPolicy(DockerCamelModel):
    condition: Optional[str] = None
    delay: Optional[int] = None
    max_attempts: Optional[int] = None
    window: Optional[int] = None


class PluginPrivilege(DockerCamelModel):
    name: Optional[str] = None
    description: Optional[str] = None
    value: Optional[List[str]] = None


class PluginSpec(DockerCamelModel):
    name: Optional[str] = None
    remote: Optional[str] = None
    disabled: Optional[bool] = None
    plugin_privilege: Optional[List[PluginPrivilege]] = None


class ContainerSpec(DockerCamelModel):
    image: Optional[str] = None
    labels: Optional[Dict[str, str]] = None
    command: Optional[List[str]] = None
    args: Optional[List[str]] = None
    hostname: Optional[str] = None
    env: Optional[List[str]] = None
    dir: Optional[str] = None
    user: Optional[str] = None
    groups: Optional[List[str]] = None
    privileges: Any = None
    tty: Annotated[Optional[bool], pydantic.Field(alias="TTY")] = None
    open_stdin: Optional[bool] = None
    read_only: Optional[bool] = None
    mounts: Optional[List[Any]] = None
    stop_signal: Optional[str] = None
    stop_grace_period: Optional[int] = None
    health_check: Any = None
    hosts: Optional[List[str]] = None
    dns_config: Any = None
    secrets: Optional[List[Any]] = None
    configs: Optional[List[Any]] = None
    isolation: Optional[str] = None
    init: Optional[bool] = None
    sysctls: Optional[Any] = None


class NetworkAttachmentSpec(DockerCamelModel):
    container_id: Annotated[Optional[str], pydantic.Field(alias="ContainerID")] = None


class ResourceObject(DockerCamelModel):
    nano_cpus: Annotated[Optional[int], pydantic.Field(alias="NanoCPUs")] = None
    memory_bytes: Optional[int] = None
    generic_resources: Optional[List[AssignedGenericResources]] = None


class Resources(DockerCamelModel):
    limits: Optional[ResourceObject] = None
    reservation: Optional[ResourceObject] = None


class TaskSpec(DockerCamelModel):
    # TODO: set types for Any
    plugin_spec: Optional[PluginSpec] = None
    container_spec: Optional[ContainerSpec] = None
    network_attachment_spec: Optional[NetworkAttachmentSpec] = None
    resources: Optional[Resources] = None
    restart_policy: Any = None
    placement: Optional[Placement] = None
    force_update: Optional[int] = None
    runtime: Optional[str] = None
    networks: Optional[List[NetworkAttachmentConfig]] = None
    log_driver: Optional[LogDriver] = None


class TaskInspectResult(DockerCamelModel):
    id: Annotated[Optional[str], pydantic.Field(alias="ID")] = None
    version: Optional[ObjectVersion] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    name: Optional[str] = None
    labels: Optional[Dict[str, str]] = None
    spec: Optional[TaskSpec] = None
    service_id: Annotated[Optional[str], pydantic.Field(alias="ServiceID")] = None
    slot: Optional[int] = None
    node_id: Annotated[Optional[str], pydantic.Field(alias="NodeID")] = None
    assigned_generic_resources: Optional[List[AssignedGenericResources]] = None
    status: Optional[TaskStatus] = None
    desired_state: Optional[str] = None
