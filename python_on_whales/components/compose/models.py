from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ServiceDeployConfig(BaseModel):
    labels: Optional[Dict[str, str]]
    resources: Any
    placement: Any


class DependencyCondition(BaseModel):
    condition: str


class ComposeConfigService(BaseModel):
    deploy: Optional[ServiceDeployConfig]
    blkio_config: Any
    cpu_count: Optional[float]
    cpu_percent: Optional[float]
    cpu_shares: Optional[int]
    cpuset: Optional[str]
    build: Any
    cap_add: List[str] = Field(default_factory=list)
    cap_drop: List[str] = Field(default_factory=list)
    cgroup_parent: Optional[str]
    command: Optional[List[str]]
    configs: Any
    container_name: Optional[str]
    depends_on: Dict[str, DependencyCondition] = Field(default_factory=dict)
    device_cgroup_rules: List[str] = Field(default_factory=list)
    devices: Any
    environment: Optional[Dict[str, Optional[str]]]
    image: Optional[str]


class ComposeConfigNetwork(BaseModel):
    driver: Optional[str]
    name: Optional[str]
    external: bool = False
    driver_opts: Optional[Dict[str, Any]]
    attachable: Optional[bool]
    enable_ipv6: Optional[bool]
    ipam: Any
    internal: Optional[bool]
    labels: Dict[str, str] = Field(default_factory=dict)


class ComposeConfigVolume(BaseModel):
    driver: Optional[str]
    driver_opts: Optional[Dict[str, Any]]
    external: Optional[bool]
    labels: Dict[str, str] = Field(default_factory=dict)
    name: Optional[str]


class ComposeConfig(BaseModel):
    services: Dict[str, ComposeConfigService]
    networks: Dict[str, ComposeConfigNetwork] = Field(default_factory=dict)
    volumes: Dict[str, ComposeConfigVolume] = Field(default_factory=dict)
    configs: Any
    secrets: Any
