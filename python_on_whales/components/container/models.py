from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pydantic

from python_on_whales.utils import DockerCamelModel, all_fields_optional


@all_fields_optional
class ContainerHealthcheckResult(DockerCamelModel):
    start: Optional[datetime]
    end: Optional[datetime]
    exit_code: Optional[int]
    output: Optional[str]


@all_fields_optional
class ContainerHealth(DockerCamelModel):
    status: Optional[str]
    failing_streak: Optional[int]
    log: Optional[List[ContainerHealthcheckResult]]


@all_fields_optional
class ContainerState(DockerCamelModel):
    status: Optional[str]
    running: Optional[bool]
    paused: Optional[bool]
    restarting: Optional[bool]
    oom_killed: Optional[bool]
    dead: Optional[bool]
    pid: Optional[int]
    exit_code: Optional[int]
    error: Optional[str]
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    health: Optional[ContainerHealth]


@all_fields_optional
class ContainerWeightDevice(DockerCamelModel):
    path: Optional[Path]
    weight: Optional[int]


@all_fields_optional
class ContainerThrottleDevice(DockerCamelModel):
    path: Optional[Path]
    rate: Optional[int]


@all_fields_optional
class ContainerDevice(DockerCamelModel):
    path_on_host: Optional[Path]
    path_in_container: Optional[Path]
    cgroup_permissions: Optional[str]


@all_fields_optional
class ContainerDeviceRequest(DockerCamelModel):
    driver: Optional[str]
    count: Optional[int]
    device_ids: Optional[List[str]] = pydantic.Field(None, alias="DeviceIDs")
    capabilities: Optional[List[Any]]
    options: Optional[Dict[str, str]]


@all_fields_optional
class ContainerUlimit(DockerCamelModel):
    name: Optional[str]
    soft: Optional[int]
    hard: Optional[int]


@all_fields_optional
class ContainerLogConfig(DockerCamelModel):
    type: Optional[str]
    config: Optional[Any]


@all_fields_optional
class ContainerRestartPolicy(DockerCamelModel):
    name: Optional[str]
    maximum_retry_count: Optional[int]


@all_fields_optional
class PortBinding(DockerCamelModel):
    host_ip: Optional[str]
    host_port: Optional[str]


@all_fields_optional
class ContainerMountBindOption(DockerCamelModel):
    propagation: Optional[str]
    non_recursive: Optional[bool]


@all_fields_optional
class ContainerVolumeDriverConfig(DockerCamelModel):
    name: Optional[str]
    options: Optional[Dict[str, Any]]


@all_fields_optional
class ContainerVolumeOptions(DockerCamelModel):
    no_copy: Optional[bool]
    labels: Optional[Dict[str, str]]


@all_fields_optional
class ContainerTmpfsOptions(DockerCamelModel):
    size_bytes: Optional[int]
    mode: Optional[int]


@all_fields_optional
class ContainerMount(DockerCamelModel):
    target: Optional[Path]
    source: Optional[str]
    type: Optional[str]
    read_only: Optional[bool]
    consistency: Optional[str]
    bind_options: Optional[ContainerMountBindOption]
    volume_options: Optional[ContainerVolumeOptions]
    tmpfs_options: Optional[ContainerTmpfsOptions]


@all_fields_optional
class ContainerHostConfig(DockerCamelModel):
    cpu_shares: Optional[int]
    memory: Optional[int]
    cgroup_parent: Optional[Path]
    blkio_weight: Optional[int]
    blkio_weight_device: Optional[List[ContainerWeightDevice]]
    blkio_device_read_bps: Optional[List[ContainerThrottleDevice]]
    blkio_device_write_bps: Optional[List[ContainerThrottleDevice]]
    blkio_device_read_iops: Optional[List[ContainerThrottleDevice]]
    blkio_device_write_iops: Optional[List[ContainerThrottleDevice]]
    cpu_period: Optional[int]
    cpu_quota: Optional[int]
    cpu_realtime_period: Optional[int]
    cpu_realtime_runtime: Optional[int]
    cpuset_cpus: Optional[str]
    cpuset_mems: Optional[str]
    devices: Optional[List[ContainerDevice]]
    device_cgroup_rules: Optional[List[str]]
    device_requests: Optional[List[ContainerDeviceRequest]]
    kernel_memory: Optional[int]
    kernel_memory_tcp: Optional[int]
    memory_reservation: Optional[int]
    memory_swap: Optional[int]
    memory_swappiness: Optional[int]
    nano_cpus: Optional[int]
    oom_kill_disable: Optional[bool]
    init: Optional[bool]
    pids_limit: Optional[int]
    ulimits: Optional[List[ContainerUlimit]]
    cpu_count: Optional[int]
    cpu_percent: Optional[int]
    binds: Optional[List[str]]
    container_id_file: Optional[Path]
    log_config: Optional[ContainerLogConfig]
    network_mode: Optional[str]
    port_bindings: Optional[Dict[str, Optional[List[PortBinding]]]]
    restart_policy: Optional[ContainerRestartPolicy]
    auto_remove: Optional[bool]
    volume_driver: Optional[str]
    volumes_from: Optional[List[str]]
    mounts: Optional[List[ContainerMount]]
    capabilities: Optional[List[str]]
    cap_add: Optional[List[str]]
    cap_drop: Optional[List[str]]
    cgroupns_mode: Optional[str]
    dns: Optional[List[str]]
    dns_options: Optional[List[str]]
    dns_search: Optional[List[str]]
    extra_hosts: Optional[List[str]]
    group_add: Optional[List[str]]
    ipc_mode: Optional[str]
    cgroup: Optional[str]
    links: Optional[List[str]]
    oom_score_adj: Optional[int]
    pid_mode: Optional[str]
    privileged: Optional[bool]
    publish_all_ports: Optional[bool]
    readonly_rootfs: Optional[bool]
    security_opt: Optional[List[str]]
    storage_opt: Any = None
    tmpfs: Optional[Dict[Path, str]]
    uts_mode: Optional[str]
    userns_mode: Optional[str]
    shm_size: Optional[int]
    sysctls: Optional[Dict[str, Any]]
    runtime: Optional[str]
    console_size: Optional[Tuple[int, int]]
    isolation: Optional[str]
    masked_paths: Optional[List[Path]]
    readonly_paths: Optional[List[Path]]


@all_fields_optional
class ContainerHealthCheck(DockerCamelModel):
    test: Optional[List[str]]
    interval: Optional[int]
    timeout: Optional[int]
    retries: Optional[int]
    start_period: Optional[int]


@all_fields_optional
class ContainerConfig(DockerCamelModel):
    hostname: Optional[str]
    domainname: Optional[str]
    user: Optional[str]
    attach_stdin: Optional[bool]
    attach_stdout: Optional[bool]
    attach_stderr: Optional[bool]
    exposed_ports: Optional[dict]
    tty: Optional[bool]
    open_stdin: Optional[bool]
    stdin_once: Optional[bool]
    env: Optional[List[str]]
    cmd: Optional[List[str]]
    healthcheck: Optional[ContainerHealthCheck]
    args_escaped: Optional[bool]
    image: Optional[str]
    volumes: Optional[dict]
    working_dir: Optional[Path]
    entrypoint: Union[List[str], str, None] = None
    network_disabled: Optional[bool]
    mac_address: Optional[str]
    on_build: Optional[List[str]]
    labels: Optional[Dict[str, str]]
    stop_signal: Optional[str]
    stop_timeout: Optional[int]
    shell: Optional[List[str]]


@all_fields_optional
class Mount(DockerCamelModel):
    type: Optional[str]
    name: Optional[str]
    source: Optional[str]
    destination: Optional[str]
    driver: Optional[str]
    mode: Optional[str]
    rw: Optional[bool]
    propagation: Optional[str]


@all_fields_optional
class ContainerEndpointIPAMConfig(DockerCamelModel):
    ipv4_address: Optional[str]
    ipv6_address: Optional[str]
    link_local_ips: Optional[List[str]]


@all_fields_optional
class NetworkInspectResult(DockerCamelModel):
    ipam_config: Optional[ContainerEndpointIPAMConfig]
    links: Optional[List[str]]
    aliases: Optional[List[str]]
    network_id: Optional[str]
    endpoint_id: Optional[str]
    gateway: Optional[str]
    ip_address: Optional[str]
    ip_prefix_length: Optional[int]
    ipv6_gateway: Optional[str]
    global_ipv6_address: Optional[str]
    global_ipv6_prefix_length: Optional[int]
    mac_address: Optional[str]
    driver_options: Optional[dict]


@all_fields_optional
class ContainerNetworkAddress(DockerCamelModel):
    addr: Optional[str]
    prefix_len: Optional[int]


@all_fields_optional
class NetworkSettings(DockerCamelModel):
    bridge: Optional[str]
    sandbox_id: Optional[str]
    hairpin_mode: Optional[bool]
    link_local_ipv6_address: Optional[str]
    link_local_ipv6_prefix_length: Optional[int]
    ports: Optional[dict]  # to rework
    sandbox_key: Optional[Path]
    secondary_ip_addresses: Optional[List[ContainerNetworkAddress]]
    secondary_ipv6_addresses: Optional[List[ContainerNetworkAddress]]
    endpoint_id: Optional[str]
    gateway: Optional[str]
    global_ipv6_address: Optional[str]
    global_ipv6_prefix_length: Optional[int]
    ip_address: Optional[str]
    ip_prefix_length: Optional[int]
    ipv6_gateway: Optional[str]
    mac_address: Optional[str]
    networks: Optional[Dict[str, NetworkInspectResult]]


@all_fields_optional
class ContainerGraphDriver(DockerCamelModel):
    name: Optional[str]
    data: Optional[Dict[str, Any]]


@all_fields_optional
class ContainerInspectResult(DockerCamelModel):
    id: Optional[str]
    created: Optional[datetime]
    path: Optional[str]
    args: Optional[List[str]]
    state: Optional[ContainerState]
    image: Optional[str]
    resolv_conf_path: Optional[str]
    hostname_path: Optional[Path]
    hosts_path: Optional[Path]
    log_path: Optional[Path]
    node: Any = None
    name: Optional[str]
    restart_count: Optional[int]
    driver: Optional[str]
    platform: Optional[str]
    mount_label: Optional[str]
    process_label: Optional[str]
    app_armor_profile: Optional[str]
    exec_ids: Optional[List[str]]
    host_config: Optional[ContainerHostConfig]
    graph_driver: Optional[ContainerGraphDriver]
    size_rw: Optional[int]
    size_root_fs: Optional[int]
    mounts: Optional[List[Mount]]
    config: Optional[ContainerConfig]
    network_settings: Optional[NetworkSettings]
