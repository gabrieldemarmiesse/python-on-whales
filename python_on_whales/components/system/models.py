from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pydantic

import python_on_whales.components.node.models
from python_on_whales.utils import DockerCamelModel, all_fields_optional


@all_fields_optional
class DockerEventActor(DockerCamelModel):
    id: Optional[str] = pydantic.Field(None, alias="ID")
    attributes: Optional[Dict[str, Any]] = pydantic.Field(None, alias="Attributes")


class DockerEvent(DockerCamelModel):
    type: Optional[str] = pydantic.Field(None, alias="Type")
    action: Optional[str] = pydantic.Field(None, alias="Action")
    actor: Optional[DockerEventActor] = pydantic.Field(None, alias="Actor")
    time: Optional[datetime] = pydantic.Field(None, alias="time")
    time_nano: Optional[int] = pydantic.Field(None, alias="timeNano")


@all_fields_optional
class DockerItemsSummary(DockerCamelModel):
    active: Optional[int]
    reclaimable: Optional[pydantic.ByteSize]
    reclaimable_percent: Optional[float]
    size: Optional[pydantic.ByteSize]
    total_count: Optional[int]


@all_fields_optional
class Plugins(DockerCamelModel):
    volume: Optional[List[str]]
    network: Optional[List[str]]
    authorization: Any = None
    log: Optional[List[str]]


@all_fields_optional
class Runtime(DockerCamelModel):
    path: Optional[str]
    runtime_args: Optional[List[str]]


@all_fields_optional
class Commit(DockerCamelModel):
    id: Optional[str] = pydantic.Field(None, alias="ID")
    expected: Optional[str]


@all_fields_optional
class RemoteManager(DockerCamelModel):
    node_id: Optional[str] = pydantic.Field(None, alias="NodeID")
    addr: Optional[str]


@all_fields_optional
class Orchestration(DockerCamelModel):
    task_history_retention_limit: Optional[int]


@all_fields_optional
class Raft(DockerCamelModel):
    snapshot_interval: Optional[int]
    keep_old_snapshots: Optional[int]
    log_entries_for_slow_followers: Optional[int]
    election_tick: Optional[int]
    heartbeat_tick: Optional[int]


@all_fields_optional
class SwarmDispatcher(DockerCamelModel):
    heartbeat_period: Optional[int]


@all_fields_optional
class SwarmCAConfig(DockerCamelModel):
    node_cert_expiry: Optional[int]
    external_ca: Optional[List[Any]] = pydantic.Field(
        None, alias="ExternalCA"
    )  # TODO: set type
    signing_ca_cert: Optional[str] = pydantic.Field(None, alias="SigningCACert")
    signing_ca_key: Optional[str] = pydantic.Field(None, alias="SigningCAKey")
    force_rotate: Optional[int]


@all_fields_optional
class SwarmEncryptionConfig(DockerCamelModel):
    auto_lock_managers: Optional[bool]


@all_fields_optional
class Driver(DockerCamelModel):
    name: Optional[str]
    options: Optional[Dict[str, Any]]


@all_fields_optional
class SwarmTasksDefault(DockerCamelModel):
    log_driver: Optional[Driver]


@all_fields_optional
class SwarmSpec(DockerCamelModel):
    name: Optional[str]
    labels: Optional[Dict[str, str]]
    orchestration: Optional[Orchestration]
    raft: Optional[Raft]
    dispatcher: Optional[SwarmDispatcher]
    ca_config: Optional[SwarmCAConfig] = pydantic.Field(None, alias="CAConfig")
    encryption_config: Optional[SwarmEncryptionConfig]
    task_defaults: Optional[SwarmTasksDefault]


@all_fields_optional
class ClusterInfo(DockerCamelModel):
    id: Optional[str] = pydantic.Field(None, alias="ID")
    version: Optional[python_on_whales.components.node.models.NodeVersion]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    spec: Optional[SwarmSpec]
    tls_info: Optional[python_on_whales.components.node.models.NodeTLSInfo]
    root_rotation_in_progress: Optional[bool]
    data_path_port: Optional[int]
    default_addr_pool: Optional[List[str]]
    subnet_size: Optional[int]


@all_fields_optional
class SwarmInfo(DockerCamelModel):
    node_id: Optional[str] = pydantic.Field(None, alias="NodeID")
    node_addr: Optional[str]
    local_node_state: Optional[str]
    control_available: Optional[bool]
    error: Optional[str]
    remote_managers: Optional[List[RemoteManager]]
    nodes: Optional[int]
    managers: Optional[int]
    cluster: Optional[ClusterInfo]


@all_fields_optional
class ClientPlugin(DockerCamelModel):
    schema_version: Optional[str]
    vendor: Optional[str]
    version: Optional[str]
    short_description: Optional[str]
    name: Optional[str]
    path: Optional[Path]
    shadowed_paths: Optional[List[Path]]


@all_fields_optional
class ClientInfo(DockerCamelModel):
    debug: Optional[bool]
    plugins: Optional[List[ClientPlugin]]
    warnings: Optional[List[str]]


@all_fields_optional
class SystemInfo(DockerCamelModel):
    id: Optional[str] = pydantic.Field(None, alias="ID")
    containers: Optional[int]
    containers_running: Optional[int]
    containers_paused: Optional[int]
    containers_stopped: Optional[int]
    images: Optional[int]
    driver: Optional[str]
    driver_status: Optional[List[List[str]]]
    docker_root_dir: Optional[Path]
    system_status: Optional[List[str]]
    plugins: Optional[Plugins]
    memory_limit: Optional[bool]
    swap_limit: Optional[bool]
    kernel_memory: Optional[bool]
    cpu_cfs_period: Optional[bool]
    cpu_cfs_quota: Optional[bool]
    cpu_shares: Optional[bool] = pydantic.Field(None, alias="CPUShares")
    cpu_set: Optional[bool] = pydantic.Field(None, alias="CPUSet")
    pids_limit: Optional[bool]
    oom_kill_disable: Optional[bool]
    ipv4_forwarding: Optional[bool] = pydantic.Field(None, alias="IPv4Forwarding")
    bridge_nf_iptables: Optional[bool]
    bridge_nf_ip6tables: Optional[bool] = pydantic.Field(
        None, alias="BridgeNfIp6tables"
    )
    debug: Optional[bool]
    nfd: Optional[int] = pydantic.Field(None, alias="NFd")
    n_goroutines: Optional[int]
    system_time: Optional[str]
    logging_driver: Optional[str]
    cgroup_driver: Optional[str]
    n_events_listener: Optional[int]
    kernel_version: Optional[str]
    operating_system: Optional[str]
    os_type: Optional[str] = pydantic.Field(None, alias="OSType")
    architecture: Optional[str]
    n_cpu: Optional[int] = pydantic.Field(None, alias="NCPU")
    mem_total: Optional[int]
    index_server_address: Optional[str]
    registry_config: Optional[Dict[str, Any]]
    generic_resources: Optional[
        List[python_on_whales.components.node.models.NodeGenericResource]
    ]

    http_proxy: Optional[str]
    https_proxy: Optional[str]
    no_proxy: Optional[str]
    name: Optional[str]
    labels: Optional[Dict[str, str]]
    experimental_build: Optional[bool]
    server_version: Optional[str]
    cluster_store: Optional[str]
    runtimes: Optional[Dict[str, Runtime]]
    default_runtime: Optional[str]
    swarm: Optional[SwarmInfo]
    live_restore_enabled: Optional[bool]
    isolation: Optional[str]
    init_binary: Optional[str]
    containerd_commit: Optional[Commit]
    runc_commit: Optional[Commit]
    init_commit: Optional[Commit]
    security_options: Optional[List[str]]
    product_license: Optional[str]
    warnings: Optional[List[str]]
    client_info: Optional[ClientInfo]
