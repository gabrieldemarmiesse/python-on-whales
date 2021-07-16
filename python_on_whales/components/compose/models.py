from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from python_on_whales.utils import all_fields_optional


@all_fields_optional
class ServiceDeployConfig(BaseModel):
    labels: Dict[str, str]
    resources: Any
    placement: Any


@all_fields_optional
class DependencyCondition(BaseModel):
    condition: str


@all_fields_optional
class ComposeConfigService(BaseModel):
    deploy: ServiceDeployConfig
    blkio_config: Any
    cpu_count: float
    cpu_percent: float
    cpu_shares: int
    cpuset: str
    build: Any
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
