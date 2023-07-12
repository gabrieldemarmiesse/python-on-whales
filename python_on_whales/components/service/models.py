from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import Field

from python_on_whales.utils import DockerCamelModel, all_fields_optional


@all_fields_optional
class CPUMemoryQuotas(DockerCamelModel):
    nano_cpus: Optional[int] = Field(None, alias="NanoCPUs")
    memory_bytes: Optional[int]


@all_fields_optional
class Resources(DockerCamelModel):
    limits: Optional[CPUMemoryQuotas]
    reservations: Optional[CPUMemoryQuotas]


@all_fields_optional
class ContainerSpec(DockerCamelModel):
    image: Optional[str]
    labels: Optional[Dict[str, str]]
    privileges: Optional[Dict[str, Optional[str]]]
    stop_grace_period: Optional[int]
    isolation: Optional[str]
    env: Optional[List[str]]


@all_fields_optional
class TaskTemplate(DockerCamelModel):
    container_spec: Optional[ContainerSpec]
    resources: Optional[Resources]


@all_fields_optional
class ChangeConfig(DockerCamelModel):
    parallelism: Optional[int]
    failure_action: Optional[str]
    monitor: Optional[int]
    max_failure_ratio: Optional[int]
    order: Optional[str]


@all_fields_optional
class ServiceSpec(DockerCamelModel):
    name: Optional[str]
    labels: Optional[Dict[str, str]]
    mode: Optional[Dict[str, Any]]
    update_config: Optional[ChangeConfig]
    rollback_config: Optional[ChangeConfig]
    task_template: Optional[TaskTemplate]


@all_fields_optional
class ServiceVersion(DockerCamelModel):
    index: Optional[int]


@all_fields_optional
class EndpointPortConfig(DockerCamelModel):
    name: Optional[str]
    protocol: Optional[str]
    target_port: Optional[int]
    published_port: Optional[int]
    publish_mode: Optional[str]


@all_fields_optional
class ServiceEndpointSpec(DockerCamelModel):
    mode: Optional[str]
    ports: Optional[List[EndpointPortConfig]]


@all_fields_optional
class VirtualIP(DockerCamelModel):
    network_id: Optional[str]
    addr: Optional[str]


@all_fields_optional
class ServiceEndpoint(DockerCamelModel):
    spec: Optional[ServiceEndpointSpec]
    ports: Optional[List[EndpointPortConfig]]
    virtual_ips: Optional[List[VirtualIP]]


@all_fields_optional
class ServiceUpdateStatus(DockerCamelModel):
    state: Optional[str]
    started_at: Optional[str]
    completed_at: Optional[str]
    message: Optional[str]


@all_fields_optional
class ServiceInspectResult(DockerCamelModel):
    id: Optional[str] = Field(None, alias="ID")
    version: Optional[ServiceVersion]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    spec: Optional[ServiceSpec]
    previous_spec: Optional[ServiceSpec]
    endpoint: Optional[ServiceEndpoint]
    update_status: Optional[ServiceUpdateStatus]
