from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pydantic

import python_on_whales.components.node.models
from python_on_whales.utils import DockerCamelModel, all_fields_optional


@all_fields_optional
class DockerEventActor(DockerCamelModel):
    id: str = pydantic.Field(alias="ID")
    attributes: Dict[str, Any]


@all_fields_optional
class DockerEvent(DockerCamelModel):
    type: str
    action: str
    actor: DockerEventActor
    time: datetime
    time_nano: int = pydantic.Field(alias="timeNano")


@all_fields_optional
class DockerItemsSummary(DockerCamelModel):
    active: int
    reclaimable: pydantic.ByteSize
    reclaimable_percent: float
    size: pydantic.ByteSize
    total_count: int


@all_fields_optional
class Plugins(DockerCamelModel):
    volume: List[str]
    network: List[str]
    authorization: Any
    log: List[str]


@all_fields_optional
class Runtime(DockerCamelModel):
    path: str
    runtime_args: List[str]


@all_fields_optional
class Commit(DockerCamelModel):
    id: str = pydantic.Field(alias="ID")
    expected: str


@all_fields_optional
class RemoteManager(DockerCamelModel):
    node_id: str = pydantic.Field(alias="NodeID")
    addr: str


@all_fields_optional
class Orchestration(DockerCamelModel):
    task_history_retention_limit: int


@all_fields_optional
class Raft(DockerCamelModel):
    snapshot_interval: int
    keep_old_snapshots: int
    log_entries_for_slow_followers: int
    election_tick: int
    heartbeat_tick: int


@all_fields_optional
class SwarmDispatcher(DockerCamelModel):
    heartbeat_period: int


@all_fields_optional
class SwarmCAConfig(DockerCamelModel):
    node_cert_expiry: int
    external_ca: List[Any] = pydantic.Field(alias="ExternalCA")  # TODO: set type
    signing_ca_cert: str = pydantic.Field(alias="SigningCACert")
    signing_ca_key: str = pydantic.Field(alias="SigningCAKey")
    force_rotate: int


@all_fields_optional
class SwarmEncryptionConfig(DockerCamelModel):
    auto_lock_managers: bool


@all_fields_optional
class Driver(DockerCamelModel):
    name: str
    options: Dict[str, Any]


@all_fields_optional
class SwarmTasksDefault(DockerCamelModel):
    log_driver: Driver


@all_fields_optional
class SwarmSpec(DockerCamelModel):
    name: str
    labels: Dict[str, str]
    orchestration: Orchestration
    raft: Raft
    dispatcher: SwarmDispatcher
    ca_config: SwarmCAConfig = pydantic.Field(alias="CAConfig")
    encryption_config: SwarmEncryptionConfig
    task_defaults: SwarmTasksDefault


@all_fields_optional
class ClusterInfo(DockerCamelModel):
    id: str = pydantic.Field(alias="ID")
    version: python_on_whales.components.node.models.NodeVersion
    created_at: datetime
    updated_at: datetime
    spec: SwarmSpec
    tls_info: python_on_whales.components.node.models.NodeTLSInfo
    root_rotation_in_progress: bool
    data_path_port: int
    default_addr_pool: List[str]
    subnet_size: int


@all_fields_optional
class SwarmInfo(DockerCamelModel):
    node_id: str = pydantic.Field(alias="NodeID")
    node_addr: str
    local_node_state: str
    control_available: bool
    error: str
    remote_managers: List[RemoteManager]
    nodes: int
    managers: int
    cluster: ClusterInfo


@all_fields_optional
class ClientPlugin(DockerCamelModel):
    schema_version: str
    vendor: str
    version: str
    short_description: str
    name: str
    path: Path
    shadowed_paths: List[Path]


@all_fields_optional
class ClientInfo(DockerCamelModel):
    debug: bool
    plugins: List[ClientPlugin]
    warnings: List[str]


@all_fields_optional
class SystemInfo(DockerCamelModel):
    id: str = pydantic.Field(alias="ID")
    containers: int
    containers_running: int
    containers_paused: int
    containers_stopped: int
    images: int
    driver: str
    driver_status: List[List[str]]
    docker_root_dir: Path
    system_status: List[str]
    plugins: Plugins
    memory_limit: bool
    swap_limit: bool
    kernel_memory: bool
    cpu_cfs_period: bool
    cpu_cfs_quota: bool
    cpu_shares: bool = pydantic.Field(alias="CPUShares")
    cpu_set: bool = pydantic.Field(alias="CPUSet")
    pids_limit: bool
    oom_kill_disable: bool
    ipv4_forwarding: bool = pydantic.Field(alias="IPv4Forwarding")
    bridge_nf_iptables: bool
    bridge_nf_ip6tables: bool = pydantic.Field(alias="BridgeNfIp6tables")
    debug: bool
    nfd: int = pydantic.Field(alias="NFd")
    n_goroutines: int
    system_time: str
    logging_driver: str
    cgroup_driver: str
    n_events_listener: int
    kernel_version: str
    operating_system: str
    os_type: str = pydantic.Field(alias="OSType")
    architecture: str
    n_cpu: int = pydantic.Field(alias="NCPU")
    mem_total: int
    index_server_address: str
    registry_config: Dict[str, Any]
    generic_resources: List[python_on_whales.components.node.models.NodeGenericResource]

    http_proxy: str
    https_proxy: str
    no_proxy: str
    name: str
    labels: Dict[str, str]
    experimental_build: bool
    server_version: str
    cluster_store: str
    runtimes: Dict[str, Runtime]
    default_runtime: str
    swarm: SwarmInfo
    live_restore_enabled: bool
    isolation: str
    init_binary: str
    containerd_commit: Commit
    runc_commit: Commit
    init_commit: Commit
    security_options: List[str]
    product_license: str
    warnings: List[str]
    client_info: ClientInfo
