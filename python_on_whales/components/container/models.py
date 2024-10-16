from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pydantic
from typing_extensions import Annotated

from python_on_whales.utils import DockerCamelModel


class ContainerHealthcheckResult(DockerCamelModel):
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    exit_code: Optional[int] = None
    output: Optional[str] = None


class ContainerHealth(DockerCamelModel):
    status: Optional[str] = None
    failing_streak: Optional[int] = None
    log: Optional[List[ContainerHealthcheckResult]] = None


class ContainerState(DockerCamelModel):
    status: Optional[str] = None
    running: Optional[bool] = None
    paused: Optional[bool] = None
    restarting: Optional[bool] = None
    oom_killed: Optional[bool] = None
    dead: Optional[bool] = None
    pid: Optional[int] = None
    exit_code: Optional[int] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    health: Optional[ContainerHealth] = None


class ContainerWeightDevice(DockerCamelModel):
    path: Optional[Path] = None
    weight: Optional[int] = None


class ContainerThrottleDevice(DockerCamelModel):
    path: Optional[Path] = None
    rate: Optional[int] = None


class ContainerDevice(DockerCamelModel):
    path_on_host: Optional[Path] = None
    path_in_container: Optional[Path] = None
    cgroup_permissions: Optional[str] = None


class ContainerDeviceRequest(DockerCamelModel):
    driver: Optional[str] = None
    count: Optional[int] = None
    device_ids: Annotated[Optional[List[str]], pydantic.Field(alias="DeviceIDs")] = None
    capabilities: Optional[List[Any]] = None
    options: Optional[Dict[str, str]] = None


class ContainerUlimit(DockerCamelModel):
    name: Optional[str] = None
    soft: Optional[int] = None
    hard: Optional[int] = None


class ContainerLogConfig(DockerCamelModel):
    type: Optional[str] = None
    config: Optional[Any] = None


class ContainerRestartPolicy(DockerCamelModel):
    name: Optional[str] = None
    maximum_retry_count: Optional[int] = None


class PortBinding(DockerCamelModel):
    host_ip: Optional[str] = None
    host_port: Optional[str] = None


class ContainerMountBindOption(DockerCamelModel):
    propagation: Optional[str] = None
    non_recursive: Optional[bool] = None


class ContainerVolumeDriverConfig(DockerCamelModel):
    name: Optional[str] = None
    options: Optional[Dict[str, Any]] = None


class ContainerVolumeOptions(DockerCamelModel):
    no_copy: Optional[bool] = None
    labels: Optional[Dict[str, str]] = None


class ContainerTmpfsOptions(DockerCamelModel):
    size_bytes: Optional[int] = None
    mode: Optional[int] = None


class ContainerMount(DockerCamelModel):
    target: Optional[Path] = None
    source: Optional[str] = None
    type: Optional[str] = None
    read_only: Optional[bool] = None
    consistency: Optional[str] = None
    bind_options: Optional[ContainerMountBindOption] = None
    volume_options: Optional[ContainerVolumeOptions] = None
    tmpfs_options: Optional[ContainerTmpfsOptions] = None


class ContainerHostConfig(DockerCamelModel):
    cpu_shares: Optional[int] = None
    memory: Optional[int] = None
    cgroup_parent: Optional[Path] = None
    blkio_weight: Optional[int] = None
    blkio_weight_device: Optional[List[ContainerWeightDevice]] = None
    blkio_device_read_bps: Optional[List[ContainerThrottleDevice]] = None
    blkio_device_write_bps: Optional[List[ContainerThrottleDevice]] = None
    blkio_device_read_iops: Optional[List[ContainerThrottleDevice]] = None
    blkio_device_write_iops: Optional[List[ContainerThrottleDevice]] = None
    cpu_period: Optional[int] = None
    cpu_quota: Optional[int] = None
    cpu_realtime_period: Optional[int] = None
    cpu_realtime_runtime: Optional[int] = None
    cpuset_cpus: Optional[str] = None
    cpuset_mems: Optional[str] = None
    devices: Optional[List[ContainerDevice]] = None
    device_cgroup_rules: Optional[List[str]] = None
    device_requests: Optional[List[ContainerDeviceRequest]] = None
    kernel_memory: Optional[int] = None
    kernel_memory_tcp: Optional[int] = None
    memory_reservation: Optional[int] = None
    memory_swap: Optional[int] = None
    memory_swappiness: Optional[int] = None
    nano_cpus: Optional[int] = None
    oom_kill_disable: Optional[bool] = None
    init: Optional[bool] = None
    pids_limit: Optional[int] = None
    ulimits: Optional[List[ContainerUlimit]] = None
    cpu_count: Optional[int] = None
    cpu_percent: Optional[int] = None
    binds: Optional[List[str]] = None
    container_id_file: Optional[Path] = None
    log_config: Optional[ContainerLogConfig] = None
    network_mode: Optional[str] = None
    port_bindings: Optional[Dict[str, Optional[List[PortBinding]]]] = None
    restart_policy: Optional[ContainerRestartPolicy] = None
    auto_remove: Optional[bool] = None
    volume_driver: Optional[str] = None
    volumes_from: Optional[List[str]] = None
    mounts: Optional[List[ContainerMount]] = None
    capabilities: Optional[List[str]] = None
    cap_add: Optional[List[str]] = None
    cap_drop: Optional[List[str]] = None
    cgroupns_mode: Optional[str] = None
    dns: Optional[List[str]] = None
    dns_options: Optional[List[str]] = None
    dns_search: Optional[List[str]] = None
    extra_hosts: Optional[List[str]] = None
    group_add: Optional[List[str]] = None
    ipc_mode: Optional[str] = None
    cgroup: Optional[str] = None
    links: Optional[List[str]] = None
    oom_score_adj: Optional[int] = None
    pid_mode: Optional[str] = None
    privileged: Optional[bool] = None
    publish_all_ports: Optional[bool] = None
    readonly_rootfs: Optional[bool] = None
    security_opt: Optional[List[str]] = None
    storage_opt: Any = None
    tmpfs: Optional[Dict[Path, str]] = None
    uts_mode: Optional[str] = None
    userns_mode: Optional[str] = None
    shm_size: Optional[int] = None
    sysctls: Optional[Dict[str, Any]] = None
    runtime: Optional[str] = None
    console_size: Optional[Tuple[int, int]] = None
    isolation: Optional[str] = None
    masked_paths: Optional[List[Path]] = None
    readonly_paths: Optional[List[Path]] = None


class ContainerHealthCheck(DockerCamelModel):
    test: Optional[List[str]] = None
    interval: Optional[int] = None
    timeout: Optional[int] = None
    retries: Optional[int] = None
    start_period: Optional[int] = None


class ContainerConfig(DockerCamelModel):
    hostname: Optional[str] = None
    domainname: Optional[str] = None
    user: Optional[str] = None
    attach_stdin: Optional[bool] = None
    attach_stdout: Optional[bool] = None
    attach_stderr: Optional[bool] = None
    exposed_ports: Optional[dict] = None
    tty: Optional[bool] = None
    open_stdin: Optional[bool] = None
    stdin_once: Optional[bool] = None
    env: Optional[List[str]] = None
    cmd: Optional[List[str]] = None
    healthcheck: Optional[ContainerHealthCheck] = None
    args_escaped: Optional[bool] = None
    image: Optional[str] = None
    volumes: Optional[dict] = None
    working_dir: Optional[Path] = None
    entrypoint: Union[List[str], str, None] = None
    network_disabled: Optional[bool] = None
    mac_address: Optional[str] = None
    on_build: Optional[List[str]] = None
    labels: Optional[Dict[str, str]] = None
    stop_signal: Optional[Union[str, int]] = None
    stop_timeout: Optional[int] = None
    shell: Optional[List[str]] = None
    systemd_mode: Optional[bool] = None


class Mount(DockerCamelModel):
    type: Optional[str] = None
    name: Optional[str] = None
    source: Optional[str] = None
    destination: Optional[str] = None
    driver: Optional[str] = None
    mode: Optional[str] = None
    rw: Optional[bool] = None
    propagation: Optional[str] = None


class ContainerEndpointIPAMConfig(DockerCamelModel):
    ipv4_address: Optional[str] = None
    ipv6_address: Optional[str] = None
    link_local_ips: Optional[List[str]] = None


class NetworkInspectResult(DockerCamelModel):
    ipam_config: Optional[ContainerEndpointIPAMConfig] = None
    links: Optional[List[str]] = None
    aliases: Optional[List[str]] = None
    network_id: Optional[str] = None
    endpoint_id: Optional[str] = None
    gateway: Optional[str] = None
    ip_address: Optional[str] = None
    ip_prefix_length: Optional[int] = None
    ipv6_gateway: Optional[str] = None
    global_ipv6_address: Optional[str] = None
    global_ipv6_prefix_length: Optional[int] = None
    mac_address: Optional[str] = None
    driver_options: Optional[dict] = None


class ContainerNetworkAddress(DockerCamelModel):
    addr: Optional[str] = None
    prefix_len: Optional[int] = None


class NetworkSettings(DockerCamelModel):
    bridge: Optional[str] = None
    sandbox_id: Optional[str] = None
    hairpin_mode: Optional[bool] = None
    link_local_ipv6_address: Optional[str] = None
    link_local_ipv6_prefix_length: Optional[int] = None
    ports: Optional[dict] = None  # to rework
    sandbox_key: Optional[Path] = None
    secondary_ip_addresses: Optional[List[ContainerNetworkAddress]] = None
    secondary_ipv6_addresses: Optional[List[ContainerNetworkAddress]] = None
    endpoint_id: Optional[str] = None
    gateway: Optional[str] = None
    global_ipv6_address: Optional[str] = None
    global_ipv6_prefix_length: Optional[int] = None
    ip_address: Optional[str] = None
    ip_prefix_length: Optional[int] = None
    ipv6_gateway: Optional[str] = None
    mac_address: Optional[str] = None
    networks: Optional[Dict[str, NetworkInspectResult]] = None


class ContainerGraphDriver(DockerCamelModel):
    name: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class ContainerInspectResult(DockerCamelModel):
    id: Optional[str] = None
    created: Optional[datetime] = None
    path: Optional[str] = None
    args: Optional[List[str]] = None
    state: Optional[ContainerState] = None
    image: Optional[str] = None
    pod: Optional[str] = None
    resolv_conf_path: Optional[str] = None
    hostname_path: Optional[Path] = None
    hosts_path: Optional[Path] = None
    log_path: Optional[Path] = None
    node: Any = None
    name: Optional[str] = None
    restart_count: Optional[int] = None
    driver: Optional[str] = None
    platform: Optional[str] = None
    mount_label: Optional[str] = None
    process_label: Optional[str] = None
    app_armor_profile: Optional[str] = None
    exec_ids: Optional[List[str]] = None
    host_config: Optional[ContainerHostConfig] = None
    graph_driver: Optional[ContainerGraphDriver] = None
    size_rw: Optional[int] = None
    size_root_fs: Optional[int] = None
    mounts: Optional[List[Mount]] = None
    config: Optional[ContainerConfig] = None
    network_settings: Optional[NetworkSettings] = None
    namespace: Optional[str] = None
    is_infra: Optional[bool] = None
