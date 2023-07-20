from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from python_on_whales.utils import all_fields_optional


@all_fields_optional
class ServicePlacement(BaseModel):
    constraints: Optional[List[str]] = None


@all_fields_optional
class ResourcesLimits(BaseModel):
    cpus: Optional[float]
    memory: Optional[int]


@all_fields_optional
class ResourcesReservation(BaseModel):
    cpus: Union[float, str, None]
    memory: Optional[int]


@all_fields_optional
class ServiceResources(BaseModel):
    limits: Optional[ResourcesLimits]
    reservations: Optional[ResourcesReservation]


@all_fields_optional
class ServiceDeployConfig(BaseModel):
    labels: Optional[Dict[str, str]]
    resources: Optional[ServiceResources]
    placement: Optional[ServicePlacement]
    replicas: Optional[int]


@all_fields_optional
class DependencyCondition(BaseModel):
    condition: Optional[str]


@all_fields_optional
class ComposeServiceBuild(BaseModel):
    context: Optional[Path]


@all_fields_optional
class ComposeServicePort(BaseModel):
    mode: Optional[str]
    protocol: Optional[str]
    published: Optional[int]
    target: Optional[int]


@all_fields_optional
class ComposeServiceVolume(BaseModel):
    bind: Optional[dict]
    source: Optional[str]
    target: Optional[str]
    type: Optional[str]


@all_fields_optional
class ComposeConfigService(BaseModel):
    deploy: Optional[ServiceDeployConfig]
    blkio_config: Optional[Any]
    cpu_count: Optional[float]
    cpu_percent: Optional[float]
    cpu_shares: Optional[int]
    cpuset: Optional[str]
    build: Optional[ComposeServiceBuild]
    cap_add: Optional[List[str]] = Field(default_factory=list)
    cap_drop: Optional[List[str]] = Field(default_factory=list)
    cgroup_parent: Optional[str]
    command: Optional[List[str]]
    configs: Any = None
    container_name: Optional[str]
    depends_on: Dict[str, DependencyCondition] = Field(default_factory=dict)
    device_cgroup_rules: List[str] = Field(default_factory=list)
    devices: Any = None
    environment: Optional[Dict[str, Optional[str]]]
    entrypoint: Optional[List[str]]
    image: Optional[str]
    labels: Optional[Dict[str, str]] = Field(default_factory=dict)
    ports: Optional[List[ComposeServicePort]]
    volumes: Optional[List[ComposeServiceVolume]]


@all_fields_optional
class ComposeConfigNetwork(BaseModel):
    driver: Optional[str]
    name: Optional[str]
    external: Optional[bool] = False
    driver_opts: Optional[Dict[str, Any]]
    attachable: Optional[bool]
    enable_ipv6: Optional[bool]
    ipam: Any = None
    internal: Optional[bool]
    labels: Dict[str, str] = Field(default_factory=dict)


@all_fields_optional
class ComposeConfigVolume(BaseModel):
    driver: Optional[str]
    driver_opts: Optional[Dict[str, Any]]
    external: Optional[bool]
    labels: Optional[Dict[str, str]] = Field(default_factory=dict)
    name: Optional[str]


@all_fields_optional
class ComposeConfig(BaseModel):
    services: Optional[Dict[str, ComposeConfigService]]
    networks: Optional[Dict[str, ComposeConfigNetwork]] = Field(default_factory=dict)
    volumes: Optional[Dict[str, ComposeConfigVolume]] = Field(default_factory=dict)
    configs: Any = None
    secrets: Any = None


class ComposeProject(BaseModel):
    name: Optional[str]
    created: Optional[int] = 0
    running: Optional[int] = 0
    restarting: Optional[int] = 0
    exited: Optional[int] = 0
    paused: Optional[int] = 0
    dead: Optional[int] = 0
    config_files: Optional[List[Path]]
