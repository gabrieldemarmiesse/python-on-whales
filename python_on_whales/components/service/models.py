from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import Field
from typing_extensions import Annotated

from python_on_whales.utils import DockerCamelModel


class CPUMemoryQuotas(DockerCamelModel):
    nano_cpus: Annotated[Optional[int], Field(alias="NanoCPUs")] = None
    memory_bytes: Optional[int] = None


class Resources(DockerCamelModel):
    limits: Optional[CPUMemoryQuotas] = None
    reservations: Optional[CPUMemoryQuotas] = None


class ContainerSpec(DockerCamelModel):
    image: Optional[str] = None
    labels: Optional[Dict[str, str]] = None
    privileges: Optional[Dict[str, Union[None, str, bool]]] = None
    stop_grace_period: Optional[int] = None
    isolation: Optional[str] = None
    env: Optional[List[str]] = None


class TaskTemplate(DockerCamelModel):
    container_spec: Optional[ContainerSpec] = None
    resources: Optional[Resources] = None


class ChangeConfig(DockerCamelModel):
    parallelism: Optional[int] = None
    failure_action: Optional[str] = None
    monitor: Optional[int] = None
    max_failure_ratio: Optional[float] = None
    order: Optional[str] = None


class ServiceSpec(DockerCamelModel):
    name: Optional[str] = None
    labels: Optional[Dict[str, str]] = None
    mode: Optional[Dict[str, Any]] = None
    update_config: Optional[ChangeConfig] = None
    rollback_config: Optional[ChangeConfig] = None
    task_template: Optional[TaskTemplate] = None


class ServiceVersion(DockerCamelModel):
    index: Optional[int] = None


class EndpointPortConfig(DockerCamelModel):
    name: Optional[str] = None
    protocol: Optional[str] = None
    target_port: Optional[int] = None
    published_port: Optional[int] = None
    publish_mode: Optional[str] = None


class ServiceEndpointSpec(DockerCamelModel):
    mode: Optional[str] = None
    ports: Optional[List[EndpointPortConfig]] = None


class VirtualIP(DockerCamelModel):
    network_id: Optional[str] = None
    addr: Optional[str] = None


class ServiceEndpoint(DockerCamelModel):
    spec: Optional[ServiceEndpointSpec] = None
    ports: Optional[List[EndpointPortConfig]] = None
    virtual_ips: Optional[List[VirtualIP]] = None


class ServiceUpdateStatus(DockerCamelModel):
    state: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    message: Optional[str] = None


class ServiceInspectResult(DockerCamelModel):
    id: Annotated[Optional[str], Field(alias="ID")] = None
    version: Optional[ServiceVersion] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    spec: Optional[ServiceSpec] = None
    previous_spec: Optional[ServiceSpec] = None
    endpoint: Optional[ServiceEndpoint] = None
    update_status: Optional[ServiceUpdateStatus] = None
