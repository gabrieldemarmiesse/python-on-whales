from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field
from typing_extensions import Annotated


class ServicePlacement(BaseModel):
    constraints: Optional[List[str]] = None


class ResourcesLimits(BaseModel):
    cpus: Optional[float] = None
    memory: Optional[int] = None


class ResourcesReservation(BaseModel):
    cpus: Union[float, int, None] = None
    memory: Optional[int] = None


class ServiceResources(BaseModel):
    limits: Optional[ResourcesLimits] = None
    reservations: Optional[ResourcesReservation] = None


class ServiceDeployConfig(BaseModel):
    labels: Optional[Dict[str, str]] = None
    resources: Optional[ServiceResources] = None
    placement: Optional[ServicePlacement] = None
    replicas: Optional[int] = None


class DependencyCondition(BaseModel):
    condition: Optional[str] = None


class ComposeServiceBuild(BaseModel):
    context: Optional[Path] = None
    dockerfile: Optional[Path] = None
    args: Optional[Dict[str, Any]] = None
    cache_from: Optional[List[str]] = None
    labels: Optional[Dict[str, Any]] = None
    network: Optional[str] = None
    shm_size: Optional[str] = None
    target: Optional[str] = None


class ComposeServiceHealthcheck(BaseModel):
    interval: Optional[str] = None
    start_period: Optional[str] = None
    start_interval: Optional[str] = None
    test: Optional[List[str]] = None
    timeout: Optional[str] = None
    retries: Optional[int] = None


class ComposeServicePort(BaseModel):
    mode: Optional[str] = None
    protocol: Optional[str] = None
    published: Optional[int] = None
    target: Optional[int] = None


class ComposeServiceULimitsNoFile(BaseModel):
    soft: Optional[int] = None
    hard: Optional[int] = None


class ComposeServiceULimits(BaseModel):
    nproc: Optional[int] = None
    nofile: Optional[ComposeServiceULimitsNoFile] = None


class ComposeServiceVolume(BaseModel):
    bind: Optional[dict] = None
    source: Optional[str] = None
    target: Optional[str] = None
    type: Optional[str] = None


class ComposeConfigService(BaseModel):
    blkio_config: Optional[Any] = None
    build: Optional[ComposeServiceBuild] = None
    cap_add: Annotated[Optional[List[str]], Field(default_factory=list)]
    cap_drop: Annotated[Optional[List[str]], Field(default_factory=list)]
    command: Optional[List[str]] = None
    cgroup_parent: Optional[str] = None
    container_name: Optional[str] = None
    cpu_count: Optional[float] = None
    cpu_percent: Optional[float] = None
    cpu_shares: Optional[int] = None
    cpuset: Optional[str] = None
    depends_on: Annotated[Dict[str, DependencyCondition], Field(default_factory=dict)]
    deploy: Optional[ServiceDeployConfig] = None
    devices: List[str] = None
    device_cgroup_rules: Annotated[List[str], Field(default_factory=list)]
    dns: Optional[List[str]] = None
    dns_search: Optional[List[str]] = None
    entrypoint: Optional[List[str]] = None
    env_file: Optional[List[str]] = None
    environment: Optional[Dict[str, Optional[str]]] = None
    expose: Optional[List[str]] = None
    external_links: Optional[List[str]] = None
    extra_hosts: Optional[List[str]] = None
    healthcheck: Optional[ComposeServiceHealthcheck] = None
    image: Optional[str] = None
    init: Optional[bool] = False
    isolation: Optional[str] = "default"
    labels: Annotated[Optional[Dict[str, str]], Field(default_factory=dict)]
    network_mode: Optional[str] = None
    networks: Optional[Union[Dict[str, Dict[str, Any]], List[str]]] = None
    pid: Optional[str] = None
    ports: Optional[List[ComposeServicePort]] = None
    profiles: Optional[List[str]] = None
    restart: str = "no"
    secrets: Optional[List[str]] = None
    stop_grace_period: str = "10s"
    stop_signal: str = "SIGTERM"
    tmpfs: Optional[List[str]] = None
    ulimits: Optional[ComposeServiceULimits] = None
    userns_mode: Optional[str] = None
    volumes: Optional[List[ComposeServiceVolume]] = None


class ComposeConfigNetwork(BaseModel):
    driver: Optional[str] = None
    name: Optional[str] = None
    external: Optional[bool] = False
    driver_opts: Optional[Dict[str, Any]] = None
    attachable: Optional[bool] = None
    enable_ipv6: Optional[bool] = None
    ipam: Any = None
    internal: Optional[bool] = None
    labels: Annotated[Dict[str, str], Field(default_factory=dict)]


class ComposeConfigVolume(BaseModel):
    driver: Optional[str] = None
    driver_opts: Optional[Dict[str, Any]] = None
    external: Optional[bool] = None
    labels: Annotated[Optional[Dict[str, str]], Field(default_factory=dict)]
    name: Optional[str] = None


class ComposeConfig(BaseModel):
    services: Optional[Dict[str, ComposeConfigService]] = None
    networks: Annotated[
        Optional[Dict[str, ComposeConfigNetwork]], Field(default_factory=dict)
    ]
    volumes: Annotated[
        Optional[Dict[str, ComposeConfigVolume]], Field(default_factory=dict)
    ]
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
    config_files: Optional[List[Path]] = None
