from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pydantic

from python_on_whales.utils import DockerCamelModel


class ContainerHealthcheckResult(DockerCamelModel):
    start: datetime
    end: datetime
    exit_code: int
    output: str


class ContainerHealth(DockerCamelModel):
    status: str
    failing_streak: int
    log: List[ContainerHealthcheckResult]


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
    health: Optional[ContainerHealth]


class ContainerWeightDevice(DockerCamelModel):
    path: Optional[Path]
    weight: Optional[int]


class ContainerThrottleDevice(DockerCamelModel):
    path: Optional[Path]
    rate: Optional[int]


class ContainerDevice(DockerCamelModel):
    path_on_host: Path
    path_in_container: Path
    cgroup_permissions: str


class ContainerDeviceRequest(DockerCamelModel):
    driver: str
    count: int
    device_ids: Optional[List[str]] = pydantic.Field(alias="DeviceIDs")
    capabilities: List[Any]
    options: Dict[str, str]


class ContainerUlimit(DockerCamelModel):
    name: Optional[str]
    soft: Optional[int]
    hard: Optional[int]


class ContainerLogConfig(DockerCamelModel):
    type: str
    config: Any


class ContainerRestartPolicy(DockerCamelModel):
    name: str
    maximum_retry_count: Optional[int]


class PortBinding(DockerCamelModel):
    host_ip: str
    host_port: str


class ContainerMountBindOption(DockerCamelModel):
    propagation: str
    non_recursive: bool


class ContainerVolumeDriverConfig(DockerCamelModel):
    name: str
    options: Dict[str, Any]


class ContainerVolumeOptions(DockerCamelModel):
    no_copy: Optional[bool]
    labels: Dict[str, str]


class ContainerTmpfsOptions(DockerCamelModel):
    size_bytes: int
    mode: int


class ContainerMount(DockerCamelModel):
    target: Path
    source: str
    type: str
    read_only: Optional[bool]
    consistency: Optional[str]
    bind_options: Optional[ContainerMountBindOption]
    volume_options: Optional[ContainerVolumeOptions]
    tmpfs_options: Optional[ContainerTmpfsOptions]


class ContainerHostConfig(DockerCamelModel):
    cpu_shares: int
    memory: int
    cgroup_parent: Optional[Path]
    blkio_weight: int
    blkio_weight_device: Optional[List[ContainerWeightDevice]]
    blkio_device_read_bps: Optional[List[ContainerThrottleDevice]]
    blkio_device_write_bps: Optional[List[ContainerThrottleDevice]]
    blkio_device_read_iops: Optional[List[ContainerThrottleDevice]]
    blkio_device_write_iops: Optional[List[ContainerThrottleDevice]]
    cpu_period: int
    cpu_quota: Optional[int]
    cpu_realtime_period: int
    cpu_realtime_runtime: int
    cpuset_cpus: str
    cpuset_mems: str
    devices: Optional[List[ContainerDevice]]
    device_cgroup_rules: Optional[List[str]]
    device_requests: Optional[List[ContainerDeviceRequest]]
    kernel_memory: int
    kernel_memory_tcp: Optional[int]
    memory_reservation: int
    memory_swap: int
    memory_swappiness: Optional[int]
    nano_cpus: Optional[int]
    oom_kill_disable: bool
    init: Optional[bool]
    pids_limit: Optional[int]
    ulimits: Optional[List[ContainerUlimit]]
    cpu_count: Optional[int]
    cpu_percent: int
    binds: Optional[List[str]]
    container_id_file: Path
    log_config: ContainerLogConfig
    network_mode: str
    port_bindings: Optional[Dict[str, Optional[List[PortBinding]]]]
    restart_policy: ContainerRestartPolicy
    auto_remove: Optional[bool]
    volume_driver: str
    volumes_from: Optional[List[str]]
    mounts: Optional[List[ContainerMount]]
    capabilities: Optional[List[str]]
    cap_add: Optional[List[str]]
    cap_drop: Optional[List[str]]
    dns: Optional[List[str]]
    dns_options: Optional[List[str]]
    dns_search: Optional[List[str]]
    extra_hosts: Optional[Dict[str, str]]
    group_add: Optional[List[str]]
    ipc_mode: str
    cgroup: Optional[str]
    links: Optional[List[str]]
    oom_score_adj: int
    pid_mode: str
    privileged: bool
    publish_all_ports: bool
    readonly_rootfs: bool
    security_opt: Optional[List[str]]
    storage_opt: Any
    tmpfs: Optional[Dict[Path, str]]
    uts_mode: Optional[str]
    userns_mode: Optional[str]
    shm_size: int
    sysctls: Optional[Dict[str, Any]]
    runtime: Optional[str]
    console_size: Optional[Tuple[int, int]]
    isolation: Optional[str]
    masked_paths: Optional[List[Path]]
    readonly_paths: Optional[List[Path]]


class ContainerHealthCheck(DockerCamelModel):
    test: List[str]
    interval: Optional[int]
    timeout: Optional[int]
    retries: Optional[int]
    start_period: Optional[int]


class ContainerConfig(DockerCamelModel):
    hostname: str
    domainname: str
    user: str
    attach_stdin: bool
    attach_stdout: bool
    attach_stderr: bool
    exposed_ports: Optional[dict]
    tty: bool
    open_stdin: bool
    stdin_once: bool
    env: Optional[List[str]]
    cmd: Optional[List[str]]
    healthcheck: Optional[ContainerHealthCheck]
    args_escaped: Optional[bool]
    image: str
    volumes: Optional[dict]
    working_dir: Path
    entrypoint: Optional[List[str]]
    network_disabled: Optional[bool]
    mac_address: Optional[str]
    on_build: Optional[List[str]]
    labels: Optional[Dict[str, str]]
    stop_signal: Optional[str]
    stop_timeout: Optional[int]
    shell: Optional[List[str]]


class Mount(DockerCamelModel):
    type: Optional[str]
    name: Optional[str]
    source: str
    destination: str
    driver: Optional[str]
    mode: str
    rw: bool
    propagation: str


class ContainerEndpointIPAMConfig(DockerCamelModel):
    ipv4_address: str
    ipv6_address: str
    link_local_ips: List[str]


class NetworkInspectResult(DockerCamelModel):
    ipam_config: Optional[ContainerEndpointIPAMConfig]
    links: Optional[List[str]]
    aliases: Optional[List[str]]
    network_id: str
    endpoint_id: str
    gateway: str
    ip_address: str
    ip_prefix_lenght: int
    ipv6_gateway: str
    global_ipv6_address: str
    global_ipv6_prefix_lenght: int
    mac_address: str
    driver_options: Optional[dict]


class ContainerNetworkAddress(DockerCamelModel):
    addr: str
    prefix_len: int


class NetworkSettings(DockerCamelModel):
    bridge: str
    sandbox_id: str
    hairpin_mode: bool
    link_local_ipv6_address: str
    link_local_ipv6_prefix_lenght: int
    ports: Optional[dict]  # to rework
    sandbox_key: Path
    secondary_ip_addresses: Optional[List[ContainerNetworkAddress]]
    secondary_ipv6_addresses: Optional[List[ContainerNetworkAddress]]
    endpoint_id: str
    gateway: str
    global_ipv6_address: str
    global_ipv6_prefix_lenght: int
    ip_adress: str
    ip_prefix_lenght: int
    ipv6_gateway: str
    mac_address: str
    networks: Dict[str, NetworkInspectResult]


class ContainerGraphDriver(DockerCamelModel):
    name: str
    data: Dict[str, Any]


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
    platform: Optional[str]
    mount_label: str
    process_label: str
    app_armor_profile: str
    exec_ids: Optional[List[str]]
    host_config: ContainerHostConfig
    graph_driver: Optional[ContainerGraphDriver]
    size_rw: Optional[int]
    size_root_fs: Optional[int]
    mounts: List[Mount]
    config: ContainerConfig
    network_settings: NetworkSettings
