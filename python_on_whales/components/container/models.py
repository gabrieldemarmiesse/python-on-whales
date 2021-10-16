from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pydantic

from python_on_whales.utils import DockerCamelModel, all_fields_optional


@all_fields_optional
class ContainerHealthcheckResult(DockerCamelModel):
    start: datetime
    end: datetime
    exit_code: int
    output: str


@all_fields_optional
class ContainerHealth(DockerCamelModel):
    status: str
    failing_streak: int
    log: List[ContainerHealthcheckResult]


@all_fields_optional
class ContainerState(DockerCamelModel):
    status: str
    running: bool
    paused: bool
    restarting: bool
    oom_killed: bool
    dead: bool
    pid: int
    exit_code: int
    error: str
    started_at: datetime
    finished_at: datetime
    health: ContainerHealth


@all_fields_optional
class ContainerWeightDevice(DockerCamelModel):
    path: Path
    weight: int


@all_fields_optional
class ContainerThrottleDevice(DockerCamelModel):
    path: Path
    rate: int


@all_fields_optional
class ContainerDevice(DockerCamelModel):
    path_on_host: Path
    path_in_container: Path
    cgroup_permissions: str


@all_fields_optional
class ContainerDeviceRequest(DockerCamelModel):
    driver: str
    count: int
    device_ids: List[str] = pydantic.Field(alias="DeviceIDs")
    capabilities: List[Any]
    options: Dict[str, str]


@all_fields_optional
class ContainerUlimit(DockerCamelModel):
    name: str
    soft: int
    hard: int


@all_fields_optional
class ContainerLogConfig(DockerCamelModel):
    type: str
    config: Any


@all_fields_optional
class ContainerRestartPolicy(DockerCamelModel):
    name: str
    maximum_retry_count: int


@all_fields_optional
class PortBinding(DockerCamelModel):
    host_ip: str
    host_port: str


@all_fields_optional
class ContainerMountBindOption(DockerCamelModel):
    propagation: str
    non_recursive: bool


@all_fields_optional
class ContainerVolumeDriverConfig(DockerCamelModel):
    name: str
    options: Dict[str, Any]


@all_fields_optional
class ContainerVolumeOptions(DockerCamelModel):
    no_copy: bool
    labels: Dict[str, str]


@all_fields_optional
class ContainerTmpfsOptions(DockerCamelModel):
    size_bytes: int
    mode: int


@all_fields_optional
class ContainerMount(DockerCamelModel):
    target: Path
    source: str
    type: str
    read_only: bool
    consistency: str
    bind_options: ContainerMountBindOption
    volume_options: ContainerVolumeOptions
    tmpfs_options: ContainerTmpfsOptions


@all_fields_optional
class ContainerHostConfig(DockerCamelModel):
    cpu_shares: int
    memory: int
    cgroup_parent: Path
    blkio_weight: int
    blkio_weight_device: List[ContainerWeightDevice]
    blkio_device_read_bps: List[ContainerThrottleDevice]
    blkio_device_write_bps: List[ContainerThrottleDevice]
    blkio_device_read_iops: List[ContainerThrottleDevice]
    blkio_device_write_iops: List[ContainerThrottleDevice]
    cpu_period: int
    cpu_quota: int
    cpu_realtime_period: int
    cpu_realtime_runtime: int
    cpuset_cpus: str
    cpuset_mems: str
    devices: List[ContainerDevice]
    device_cgroup_rules: List[str]
    device_requests: List[ContainerDeviceRequest]
    kernel_memory: int
    kernel_memory_tcp: int
    memory_reservation: int
    memory_swap: int
    memory_swappiness: int
    nano_cpus: int
    oom_kill_disable: bool
    init: bool
    pids_limit: int
    ulimits: List[ContainerUlimit]
    cpu_count: int
    cpu_percent: int
    binds: List[str]
    container_id_file: Path
    log_config: ContainerLogConfig
    network_mode: str
    port_bindings: Dict[str, List[PortBinding]]
    restart_policy: ContainerRestartPolicy
    auto_remove: bool
    volume_driver: str
    volumes_from: List[str]
    mounts: List[ContainerMount]
    capabilities: List[str]
    cap_add: List[str]
    cap_drop: List[str]
    dns: List[str]
    dns_options: List[str]
    dns_search: List[str]
    extra_hosts: List[str]
    group_add: List[str]
    ipc_mode: str
    cgroup: str
    links: List[str]
    oom_score_adj: int
    pid_mode: str
    privileged: bool
    publish_all_ports: bool
    readonly_rootfs: bool
    security_opt: List[str]
    storage_opt: Any
    tmpfs: Dict[Path, str]
    uts_mode: str
    userns_mode: str
    shm_size: int
    sysctls: Dict[str, Any]
    runtime: str
    console_size: Tuple[int, int]
    isolation: str
    masked_paths: List[Path]
    readonly_paths: List[Path]


@all_fields_optional
class ContainerHealthCheck(DockerCamelModel):
    test: List[str]
    interval: int
    timeout: int
    retries: int
    start_period: int


@all_fields_optional
class ContainerConfig(DockerCamelModel):
    hostname: str
    domainname: str
    user: str
    attach_stdin: bool
    attach_stdout: bool
    attach_stderr: bool
    exposed_ports: dict
    tty: bool
    open_stdin: bool
    stdin_once: bool
    env: List[str]
    cmd: List[str]
    healthcheck: ContainerHealthCheck
    args_escaped: bool
    image: str
    volumes: dict
    working_dir: Path
    entrypoint: List[str]
    network_disabled: bool
    mac_address: str
    on_build: List[str]
    labels: Dict[str, str]
    stop_signal: str
    stop_timeout: int
    shell: List[str]


@all_fields_optional
class Mount(DockerCamelModel):
    type: str
    name: str
    source: str
    destination: str
    driver: str
    mode: str
    rw: bool
    propagation: str


@all_fields_optional
class ContainerEndpointIPAMConfig(DockerCamelModel):
    ipv4_address: str
    ipv6_address: str
    link_local_ips: List[str]


@all_fields_optional
class NetworkInspectResult(DockerCamelModel):
    ipam_config: ContainerEndpointIPAMConfig
    links: List[str]
    aliases: List[str]
    network_id: str
    endpoint_id: str
    gateway: str
    ip_address: str
    ip_prefix_lenght: int
    ipv6_gateway: str
    global_ipv6_address: str
    global_ipv6_prefix_lenght: int
    mac_address: str
    driver_options: dict


@all_fields_optional
class ContainerNetworkAddress(DockerCamelModel):
    addr: str
    prefix_len: int


@all_fields_optional
class NetworkSettings(DockerCamelModel):
    bridge: str
    sandbox_id: str
    hairpin_mode: bool
    link_local_ipv6_address: str
    link_local_ipv6_prefix_lenght: int
    ports: dict  # to rework
    sandbox_key: Path
    secondary_ip_addresses: List[ContainerNetworkAddress]
    secondary_ipv6_addresses: List[ContainerNetworkAddress]
    endpoint_id: str
    gateway: str
    global_ipv6_address: str
    global_ipv6_prefix_lenght: int
    ip_address: str
    ip_prefix_lenght: int
    ipv6_gateway: str
    mac_address: str
    networks: Dict[str, NetworkInspectResult]


@all_fields_optional
class ContainerGraphDriver(DockerCamelModel):
    name: str
    data: Dict[str, Any]


@all_fields_optional
class ContainerInspectResult(DockerCamelModel):
    id: str
    created: datetime
    path: str
    args: List[str]
    state: ContainerState
    image: str
    resolv_conf_path: str
    hostname_path: Path
    hosts_path: Path
    log_path: Path
    node: Any
    name: str
    restart_count: int
    driver: str
    platform: str
    mount_label: str
    process_label: str
    app_armor_profile: str
    exec_ids: List[str]
    host_config: ContainerHostConfig
    graph_driver: ContainerGraphDriver
    size_rw: int
    size_root_fs: int
    mounts: List[Mount]
    config: ContainerConfig
    network_settings: NetworkSettings
