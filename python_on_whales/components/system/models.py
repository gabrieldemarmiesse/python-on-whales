from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pydantic
from typing_extensions import Annotated

import python_on_whales.components.node.models
from python_on_whales.utils import DockerCamelModel


class DockerEventActor(DockerCamelModel):
    id: Annotated[Optional[str], pydantic.Field(alias="ID")] = None
    attributes: Annotated[
        Optional[Dict[str, Any]], pydantic.Field(alias="Attributes")
    ] = None


class DockerEvent(DockerCamelModel):
    type: Annotated[Optional[str], pydantic.Field(alias="Type")] = None
    action: Annotated[Optional[str], pydantic.Field(alias="Action")] = None
    actor: Annotated[Optional[DockerEventActor], pydantic.Field(alias="Actor")] = None
    time: Annotated[Optional[datetime], pydantic.Field(alias="time")] = None
    time_nano: Annotated[Optional[int], pydantic.Field(alias="timeNano")] = None


class DockerItemsSummary(DockerCamelModel):
    active: Optional[int] = None
    reclaimable: Optional[pydantic.ByteSize] = None
    reclaimable_percent: Optional[float] = None
    size: Optional[pydantic.ByteSize] = None
    total_count: Optional[int] = None


class Plugins(DockerCamelModel):
    volume: Optional[List[str]] = None
    network: Optional[List[str]] = None
    authorization: Any = None
    log: Optional[List[str]] = None


class Runtime(DockerCamelModel):
    path: Optional[str] = None
    runtime_args: Optional[List[str]] = None


class Commit(DockerCamelModel):
    id: Annotated[Optional[str], pydantic.Field(alias="ID")] = None
    expected: Optional[str] = None


class RemoteManager(DockerCamelModel):
    node_id: Annotated[Optional[str], pydantic.Field(alias="NodeID")] = None
    addr: Optional[str] = None


class Orchestration(DockerCamelModel):
    task_history_retention_limit: Optional[int] = None


class Raft(DockerCamelModel):
    snapshot_interval: Optional[int] = None
    keep_old_snapshots: Optional[int] = None
    log_entries_for_slow_followers: Optional[int] = None
    election_tick: Optional[int] = None
    heartbeat_tick: Optional[int] = None


class SwarmDispatcher(DockerCamelModel):
    heartbeat_period: Optional[int] = None


class SwarmCAConfig(DockerCamelModel):
    node_cert_expiry: Optional[int] = None
    external_ca: Annotated[Optional[List[Any]], pydantic.Field(alias="ExternalCA")] = (
        None  # TODO: set type
    )
    signing_ca_cert: Annotated[Optional[str], pydantic.Field(alias="SigningCACert")] = (
        None
    )
    signing_ca_key: Annotated[Optional[str], pydantic.Field(alias="SigningCAKey")] = (
        None
    )
    force_rotate: Optional[int] = None


class SwarmEncryptionConfig(DockerCamelModel):
    auto_lock_managers: Optional[bool] = None


class Driver(DockerCamelModel):
    name: Optional[str] = None
    options: Optional[Dict[str, Any]] = None


class SwarmTasksDefault(DockerCamelModel):
    log_driver: Optional[Driver] = None


class SwarmSpec(DockerCamelModel):
    name: Optional[str] = None
    labels: Optional[Dict[str, str]] = None
    orchestration: Optional[Orchestration] = None
    raft: Optional[Raft] = None
    dispatcher: Optional[SwarmDispatcher] = None
    ca_config: Annotated[Optional[SwarmCAConfig], pydantic.Field(alias="CAConfig")] = (
        None
    )
    encryption_config: Optional[SwarmEncryptionConfig] = None
    task_defaults: Optional[SwarmTasksDefault] = None


class ClusterInfo(DockerCamelModel):
    id: Annotated[Optional[str], pydantic.Field(alias="ID")]
    version: Optional[python_on_whales.components.node.models.NodeVersion] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    spec: Optional[SwarmSpec] = None
    tls_info: Optional[python_on_whales.components.node.models.NodeTLSInfo] = None
    root_rotation_in_progress: Optional[bool] = None
    data_path_port: Optional[int] = None
    default_addr_pool: Optional[List[str]] = None
    subnet_size: Optional[int] = None


class SwarmInfo(DockerCamelModel):
    node_id: Annotated[Optional[str], pydantic.Field(alias="NodeID")] = None
    node_addr: Optional[str] = None
    local_node_state: Optional[str] = None
    control_available: Optional[bool] = None
    error: Optional[str] = None
    remote_managers: Optional[List[RemoteManager]] = None
    nodes: Optional[int] = None
    managers: Optional[int] = None
    cluster: Optional[ClusterInfo] = None


class ClientPlugin(DockerCamelModel):
    schema_version: Optional[str] = None
    vendor: Optional[str] = None
    version: Optional[str] = None
    short_description: Optional[str] = None
    name: Optional[str] = None
    path: Optional[Path] = None
    shadowed_paths: Optional[List[Path]] = None


class ClientInfo(DockerCamelModel):
    debug: Optional[bool] = None
    plugins: Optional[List[ClientPlugin]] = None
    warnings: Optional[List[str]] = None


class SystemInfo(DockerCamelModel):
    id: Annotated[Optional[str], pydantic.Field(alias="ID")] = None
    containers: Optional[int] = None
    containers_running: Optional[int] = None
    containers_paused: Optional[int] = None
    containers_stopped: Optional[int] = None
    images: Optional[int] = None
    driver: Optional[str] = None
    driver_status: Optional[List[List[str]]] = None
    docker_root_dir: Optional[Path] = None
    system_status: Optional[List[str]] = None
    plugins: Optional[Plugins] = None
    memory_limit: Optional[bool] = None
    swap_limit: Optional[bool] = None
    kernel_memory: Optional[bool] = None
    cpu_cfs_period: Optional[bool] = None
    cpu_cfs_quota: Optional[bool] = None
    cpu_shares: Annotated[Optional[bool], pydantic.Field(alias="CPUShares")] = None
    cpu_set: Annotated[Optional[bool], pydantic.Field(alias="CPUSet")] = None
    pids_limit: Optional[bool] = None
    oom_kill_disable: Optional[bool] = None
    ipv4_forwarding: Annotated[
        Optional[bool], pydantic.Field(alias="IPv4Forwarding")
    ] = None
    bridge_nf_iptables: Optional[bool] = None
    bridge_nf_ip6tables: Annotated[
        Optional[bool], pydantic.Field(alias="BridgeNfIp6tables")
    ] = None
    debug: Optional[bool] = None
    nfd: Annotated[Optional[int], pydantic.Field(alias="NFd")] = None
    n_goroutines: Optional[int] = None
    system_time: Optional[str] = None
    logging_driver: Optional[str] = None
    cgroup_driver: Optional[str] = None
    n_events_listener: Optional[int] = None
    kernel_version: Optional[str] = None
    operating_system: Optional[str] = None
    os_type: Annotated[Optional[str], pydantic.Field(alias="OSType")] = None
    architecture: Optional[str] = None
    n_cpu: Annotated[Optional[int], pydantic.Field(alias="NCPU")] = None
    mem_total: Optional[int] = None
    index_server_address: Optional[str] = None
    registry_config: Optional[Dict[str, Any]] = None
    generic_resources: Optional[
        List[python_on_whales.components.node.models.NodeGenericResource]
    ] = None

    http_proxy: Optional[str] = None
    https_proxy: Optional[str] = None
    no_proxy: Optional[str] = None
    name: Optional[str] = None
    labels: Optional[List[str]] = None
    experimental_build: Optional[bool] = None
    server_version: Optional[str] = None
    cluster_store: Optional[str] = None
    runtimes: Optional[Dict[str, Runtime]] = None
    default_runtime: Optional[str] = None
    swarm: Optional[SwarmInfo] = None
    live_restore_enabled: Optional[bool] = None
    isolation: Optional[str] = None
    init_binary: Optional[str] = None
    containerd_commit: Optional[Commit] = None
    runc_commit: Optional[Commit] = None
    init_commit: Optional[Commit] = None
    security_options: Optional[List[str]] = None
    product_license: Optional[str] = None
    warnings: Optional[List[str]] = None
    client_info: Optional[ClientInfo] = None
