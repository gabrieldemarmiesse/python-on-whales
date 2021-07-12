from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import Field

from python_on_whales.utils import DockerCamelModel, all_fields_optional


@all_fields_optional
class CPUMemoryQuotas(DockerCamelModel):
    nano_cpus: int = Field(alias="NanoCPUs")
    memory_bytes: int


@all_fields_optional
class Resources(DockerCamelModel):
    limits: CPUMemoryQuotas
    reservations: CPUMemoryQuotas


@all_fields_optional
class ContainerSpec(DockerCamelModel):
    image: str
    labels: Dict[str, str]
    privileges: Dict[str, Optional[str]]
    stop_grace_period: int
    isolation: str
    env: List[str]


@all_fields_optional
class TaskTemplate(DockerCamelModel):
    container_spec: ContainerSpec
    resources: Resources


@all_fields_optional
class ChangeConfig(DockerCamelModel):
    parallelism: int
    failure_action: str
    monitor: int
    max_failure_ratio: int
    order: str


@all_fields_optional
class ServiceSpec(DockerCamelModel):
    name: str
    labels: Dict[str, str]
    mode: Dict[str, Any]
    update_config: ChangeConfig
    rollback_config: ChangeConfig
    task_template: TaskTemplate


@all_fields_optional
class ServiceVersion(DockerCamelModel):
    index: int


@all_fields_optional
class EndpointPortConfig(DockerCamelModel):
    name: str
    protocol: str
    target_port: int
    published_port: int
    publish_mode: str


@all_fields_optional
class ServiceEndpointSpec(DockerCamelModel):
    mode: str
    ports: List[EndpointPortConfig]


@all_fields_optional
class VirtualIP(DockerCamelModel):
    network_id: str
    addr: str


@all_fields_optional
class ServiceEndpoint(DockerCamelModel):
    spec: ServiceEndpointSpec
    ports: List[EndpointPortConfig]
    virtual_ips: List[VirtualIP]


@all_fields_optional
class ServiceUpdateStatus(DockerCamelModel):
    state: str
    started_at: str
    completed_at: str
    message: str


@all_fields_optional
class ServiceInspectResult(DockerCamelModel):
    id: str = Field(alias="ID")
    version: ServiceVersion
    created_at: datetime
    updated_at: datetime
    spec: ServiceSpec
    previous_spec: ServiceSpec
    endpoint: ServiceEndpoint
    update_status: ServiceUpdateStatus
