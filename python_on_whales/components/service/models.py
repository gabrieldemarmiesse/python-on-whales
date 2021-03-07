from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import Field

from python_on_whales.utils import DockerCamelModel


class CPUMemoryQuotas(DockerCamelModel):
    nano_cpus: Optional[int] = Field(alias="NanoCPUs")
    memory_bytes: Optional[int]


class Resources(DockerCamelModel):
    limits: Optional[CPUMemoryQuotas]
    reservations: Optional[CPUMemoryQuotas]


class ContainerSpec(DockerCamelModel):
    image: str
    labels: Optional[Dict[str, str]]
    privileges: Optional[Dict[str, Optional[str]]]
    stop_grace_period: Optional[int]
    isolation: Optional[str]
    env: Optional[List[str]]


class TaskTemplate(DockerCamelModel):
    container_spec: ContainerSpec
    resources: Resources


class ChangeConfig(DockerCamelModel):
    parallelism: int
    failure_action: str
    monitor: Optional[int]
    max_failure_ratio: Optional[int]
    order: Optional[str]


class ServiceSpec(DockerCamelModel):
    name: str
    labels: Optional[Dict[str, str]]
    mode: Optional[Dict[str, Any]]
    update_config: Optional[ChangeConfig]
    rollback_config: Optional[ChangeConfig]
    task_template: TaskTemplate


class ServiceVersion(DockerCamelModel):
    index: int


class EndpointPortConfig(DockerCamelModel):
    name: Optional[str]
    protocol: str
    target_port: int
    published_port: Optional[int]
    publish_mode: Optional[str]


class ServiceEndpointSpec(DockerCamelModel):
    mode: Optional[str]
    ports: Optional[List[EndpointPortConfig]]


class VirtualIP(DockerCamelModel):
    network_id: str
    addr: str


class ServiceEndpoint(DockerCamelModel):
    spec: ServiceEndpointSpec
    ports: Optional[List[EndpointPortConfig]]
    virtual_ips: Optional[List[VirtualIP]]


class ServiceUpdateStatus(DockerCamelModel):
    state: str
    started_at: str
    completed_at: Optional[str]
    message: str


class ServiceInspectResult(DockerCamelModel):
    id: str = Field(alias="ID")
    version: ServiceVersion
    created_at: datetime
    updated_at: datetime
    spec: ServiceSpec
    previous_spec: Optional[ServiceSpec]
    endpoint: ServiceEndpoint
    update_status: Optional[ServiceUpdateStatus]
