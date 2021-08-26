from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from python_on_whales.utils import all_fields_optional


@all_fields_optional
class ServicePlacement(BaseModel):
    constraints: List[str]


@all_fields_optional
class ResourcesLimits(BaseModel):
    cpus: float
    memory: int


@all_fields_optional
class ResourcesReservation(BaseModel):
    cpus: Union[float, str]
    memory: int


@all_fields_optional
class ServiceResources(BaseModel):
    limits: ResourcesLimits
    reservations: ResourcesReservation


@all_fields_optional
class ServiceDeployConfig(BaseModel):
    labels: Dict[str, str]
    resources: ServiceResources
    placement: ServicePlacement
    replicas: int


@all_fields_optional
class DependencyCondition(BaseModel):
    condition: str


@all_fields_optional
class ComposeServiceBuild(BaseModel):
    context: Path


@all_fields_optional
class ComposeServicePort(BaseModel):
    mode: str
    protocol: str
    published: int
    target: int


@all_fields_optional
class ComposeServiceVolume(BaseModel):
    bind: dict
    source: str
    target: str
    type: str


@all_fields_optional
class ComposeConfigService(BaseModel):
    deploy: ServiceDeployConfig
    blkio_config: Any
    cpu_count: float
    cpu_percent: float
    cpu_shares: int
    cpuset: str
    build: ComposeServiceBuild
    cap_add: List[str] = Field(default_factory=list)
    cap_drop: List[str] = Field(default_factory=list)
    cgroup_parent: str
    command: List[str]
    configs: Any
    container_name: str
    depends_on: Dict[str, DependencyCondition] = Field(default_factory=dict)
    device_cgroup_rules: List[str] = Field(default_factory=list)
    devices: Any
    environment: Dict[str, Optional[str]]
    entrypoint: List[str]
    image: str
    labels: Dict[str, str] = Field(default_factory=dict)
    ports: List[ComposeServicePort]
    volumes: List[ComposeServiceVolume]


@all_fields_optional
class ComposeConfigNetwork(BaseModel):
    driver: str
    name: str
    external: bool = False
    driver_opts: Dict[str, Any]
    attachable: bool
    enable_ipv6: bool
    ipam: Any
    internal: bool
    labels: Dict[str, str] = Field(default_factory=dict)


@all_fields_optional
class ComposeConfigVolume(BaseModel):
    driver: str
    driver_opts: Dict[str, Any]
    external: bool
    labels: Dict[str, str] = Field(default_factory=dict)
    name: str


@all_fields_optional
class ComposeConfig(BaseModel):
    services: Dict[str, ComposeConfigService]
    networks: Dict[str, ComposeConfigNetwork] = Field(default_factory=dict)
    volumes: Dict[str, ComposeConfigVolume] = Field(default_factory=dict)
    configs: Any
    secrets: Any
