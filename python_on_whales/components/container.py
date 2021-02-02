from __future__ import annotations

import inspect
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union, overload

import pydantic

import python_on_whales.components.image
import python_on_whales.components.network
import python_on_whales.components.volume
from python_on_whales.client_config import (
    ClientConfig,
    DockerCLICaller,
    ReloadableObjectFromJson,
)
from python_on_whales.utils import (
    DockerCamelModel,
    ValidPath,
    format_dict_for_cli,
    removeprefix,
    run,
    stream_stdout_and_stderr,
    to_list,
)


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
    path: Path
    weight: int


class ContainerThrottleDevice(DockerCamelModel):
    path: Path
    rate: int


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
    name: str
    soft: int
    hard: int


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
    cgroup_parent: Path
    blkio_weight: int
    blkio_weight_device: Optional[List[ContainerWeightDevice]]
    blkio_device_read_bps: Optional[List[ContainerThrottleDevice]]
    blkio_device_write_bps: Optional[List[ContainerThrottleDevice]]
    blkio_device_read_iops: Optional[List[ContainerThrottleDevice]]
    blkio_device_write_iops: Optional[List[ContainerThrottleDevice]]
    cpu_period: int
    cpu_quota: int
    cpu_realtime_period: int
    cpu_realtime_runtime: int
    cpuset_cpus: str
    cpuset_mems: str
    devices: Optional[List[ContainerDevice]]
    device_cgroup_rules: Optional[List[str]]
    device_requests: Optional[List[ContainerDeviceRequest]]
    kernel_memory: int
    kernel_memory_tcp: int
    memory_reservation: int
    memory_swap: int
    memory_swappiness: Optional[int]
    nano_cpus: int
    oom_kill_disable: bool
    init: Optional[bool]
    pids_limit: Optional[int]
    ulimits: Optional[List[ContainerUlimit]]
    cpu_count: int
    cpu_percent: int
    binds: Optional[List[str]]
    container_id_file: Path
    log_config: ContainerLogConfig
    network_mode: str
    port_bindings: Optional[Dict[str, Optional[List[PortBinding]]]]
    restart_policy: ContainerRestartPolicy
    auto_remove: bool
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
    cgroup: str
    links: Optional[List[str]]
    oom_score_adj: int
    pid_mode: str
    privileged: bool
    publish_all_ports: bool
    readonly_rootfs: bool
    security_opt: Optional[List[str]]
    storage_opt: Any
    tmpfs: Optional[Dict[Path, str]]
    uts_mode: str
    userns_mode: str
    shm_size: int
    sysctls: Optional[Dict[str, Any]]
    runtime: str
    console_size: Tuple[int, int]
    isolation: Optional[str]
    masked_paths: Optional[List[Path]]
    readonly_paths: Optional[List[Path]]


class ContainerHealthCheck(DockerCamelModel):
    test: List[str]
    interval: int
    timeout: int
    retries: int
    start_period: int


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
    type: str
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
    ports: dict  # to rework
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
    platform: str
    mount_label: str
    process_label: str
    app_armor_profile: str
    exec_ids: Optional[List[str]]
    host_config: ContainerHostConfig
    graph_driver: ContainerGraphDriver
    size_rw: Optional[int]
    size_root_fs: Optional[int]
    mounts: List[Mount]
    config: ContainerConfig
    network_settings: NetworkSettings


class Container(ReloadableObjectFromJson):
    def __init__(
        self, client_config: ClientConfig, reference: str, is_immutable_id=False
    ):
        super().__init__(client_config, "id", reference, is_immutable_id)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        autoremove = self.host_config.auto_remove
        if self.state.running:
            self.stop()
        if not autoremove:
            self.remove(volumes=True)

    def _fetch_inspect_result_json(self, reference):
        return run(self.docker_cmd + ["container", "inspect", reference])

    def _parse_json_object(self, json_object: Dict[str, Any]):
        return ContainerInspectResult.parse_obj(json_object)

    def _get_inspect_result(self) -> ContainerInspectResult:
        """Only there to allow tools to know the return type"""
        return super()._get_inspect_result()

    # ----------------------------------------------------------------
    # attributes taken from the json inspect result
    @property
    def id(self) -> str:
        return self._get_immutable_id()

    @property
    def created(self) -> datetime:
        return self._get_inspect_result().created

    @property
    def path(self) -> str:
        return self._get_inspect_result().path

    @property
    def args(self) -> List[str]:
        return self._get_inspect_result().args

    @property
    def state(self) -> ContainerState:
        return self._get_inspect_result().state

    @property
    def image(self) -> str:
        return self._get_inspect_result().image

    @property
    def resolv_conf_path(self) -> str:
        return self._get_inspect_result().resolv_conf_path

    @property
    def hostname_path(self) -> Path:
        return self._get_inspect_result().hostname_path

    @property
    def hosts_path(self) -> Path:
        return self._get_inspect_result().hosts_path

    @property
    def log_path(self) -> Path:
        return self._get_inspect_result().log_path

    @property
    def node(self) -> Any:
        return self._get_inspect_result().node

    @property
    def name(self) -> str:
        return removeprefix(self._get_inspect_result().name, "/")

    @property
    def restart_count(self) -> int:
        return self._get_inspect_result().restart_count

    @property
    def driver(self) -> str:
        return self._get_inspect_result().driver

    @property
    def platform(self) -> str:
        return self._get_inspect_result().platform

    @property
    def mount_label(self) -> str:
        return self._get_inspect_result().mount_label

    @property
    def process_label(self) -> str:
        return self._get_inspect_result().process_label

    @property
    def app_armor_profile(self) -> str:
        return self._get_inspect_result().app_armor_profile

    @property
    def exec_ids(self) -> Optional[List[str]]:
        return self._get_inspect_result().exec_ids

    @property
    def host_config(self) -> ContainerHostConfig:
        return self._get_inspect_result().host_config

    @property
    def graph_driver(self) -> ContainerGraphDriver:
        return self._get_inspect_result().graph_driver

    @property
    def size_rw(self) -> Optional[int]:
        return self._get_inspect_result().size_rw

    @property
    def size_root_fs(self) -> Optional[int]:
        return self._get_inspect_result().size_root_fs

    @property
    def mounts(self) -> List[Mount]:
        return self._get_inspect_result().mounts

    @property
    def config(self) -> ContainerConfig:
        return self._get_inspect_result().config

    @property
    def network_settings(self) -> NetworkSettings:
        return self._get_inspect_result().network_settings

    # --------------------------------------------------------------------
    # public methods

    def commit(
        self,
        tag: Optional[str] = None,
        author: Optional[str] = None,
        message: Optional[str] = None,
        pause: bool = True,
    ) -> python_on_whales.components.image.Image:
        """Create a new image from the container's changes.

        Alias: `docker.commit(...)`

        See the [`docker.container.commit`](../sub-commands/container.md) command for
        information about the arguments.
        """
        return ContainerCLI(self.client_config).commit(
            self, tag, author, message, pause
        )

    def copy_from(self, container_path: ValidPath, local_path: ValidPath):
        return ContainerCLI(self.client_config).copy((self, container_path), local_path)

    def copy_to(self, local_path: ValidPath, container_path: ValidPath):
        return ContainerCLI(self.client_config).copy(local_path, (self, container_path))

    def diff(self) -> Dict[str, str]:
        """Returns the diff of this container filesystem.

        See the [`docker.container.diff`](../sub-commands/container.md) command for
        information about the arguments.
        """
        return ContainerCLI(self.client_config).diff(self)

    def execute(self, command: Union[str, List[str]], detach: bool = False):
        """Execute a command in this container

        See the [`docker.container.execute`](../sub-commands/container.md#execute)
        command for information about the arguments.
        """
        return ContainerCLI(self.client_config).execute(self, command, detach)

    def export(self, output: ValidPath) -> None:
        """Export this container filesystem.

        See the [`docker.container.export`](../sub-commands/container.md) command for
        information about the arguments.
        """
        return ContainerCLI(self.client_config).export(self, output)

    def kill(self, signal: str = None):
        """Kill this container

        See the [`docker.container.kill`](../sub-commands/container.md#kill) command for
        information about the arguments.
        """
        return ContainerCLI(self.client_config).kill(self, signal)

    def logs(
        self,
        details: bool = False,
        since: Union[None, datetime, timedelta] = None,
        tail: Optional[int] = None,
        timestamps: bool = False,
        until: Union[None, datetime, timedelta] = None,
    ) -> str:
        """Returns the logs of the container

        See the [`docker.container.logs`](../sub-commands/container.md#logs) command for
        information about the arguments.
        """
        return ContainerCLI(self.client_config).logs(
            self, details, since, tail, timestamps, until
        )

    def pause(self) -> None:
        """Pause this container.

        See the [`docker.container.pause`](../sub-commands/container.md#pause) command for
        information about the arguments.
        """
        return ContainerCLI(self.client_config).pause(self)

    def unpause(self) -> None:
        """Unpause the container

        See the [`docker.container.unpause`](../sub-commands/container.md#unpause) command for
        information about the arguments.
        """
        return ContainerCLI(self.client_config).unpause(self)

    def rename(self, new_name: str) -> None:
        """Rename this container

        See the [`docker.container.rename`](../sub-commands/container.md#rename) command for
        information about the arguments.
        """
        return ContainerCLI(self.client_config).rename(self, new_name)

    def restart(self, time: Optional[Union[int, timedelta]] = None) -> None:
        """Restarts this container.

        See the [`docker.container.restart`](../sub-commands/container.md#restart) command for
        information about the arguments.
        """
        return ContainerCLI(self.client_config).restart(self, time)

    def remove(self, force: bool = False, volumes: bool = False) -> None:
        """Remove this container.

        See the [`docker.container.remove`](../sub-commands/container.md#remove) command for
        information about the arguments.
        """
        return ContainerCLI(self.client_config).remove(self, force, volumes)

    def start(
        self, attach: bool = False, stream: bool = False
    ) -> Union[None, str, Iterable[Tuple[str, bytes]]]:
        """Starts this container.

        See the [`docker.container.start`](../sub-commands/container.md#start) command for
        information about the arguments.
        """
        return ContainerCLI(self.client_config).start(self, attach, stream)

    def stop(self, time: Union[int, timedelta] = None) -> None:
        """Stops this container.

        See the [`docker.container.stop`](../sub-commands/container.md#stop) command for
        information about the arguments.
        """
        return ContainerCLI(self.client_config).stop(self, time)


ContainerPath = Tuple[Union[Container, str], ValidPath]
ValidContainer = Union[Container, str]
ValidPortMapping = Union[
    Tuple[Union[str, int], Union[str, int]],
    Tuple[Union[str, int], Union[str, int], str],
]


class ContainerCLI(DockerCLICaller):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.remove = self.remove

    def attach(self):
        """Not yet implemented"""
        raise NotImplementedError

    def commit(
        self,
        container: ValidContainer,
        tag: Optional[str] = None,
        author: Optional[str] = None,
        message: Optional[str] = None,
        pause: bool = True,
    ) -> python_on_whales.components.image.Image:
        """Create a new image from a container's changes

        # Arguments
            container: The container to create the image from
            tag: tag to apply on the image produced
            author: Author (e.g., "John Hannibal Smith <hannibal@a-team.com>")
            message: Commit message
            pause: Pause container during commit
        """
        full_cmd = self.docker_cmd + ["container", "commit"]

        if author is not None:
            full_cmd += ["--author", author]

        if message is not None:
            full_cmd += ["--message", message]

        # TODO: fixme
        # full_cmd += ["--pause", str(pause).lower()]

        full_cmd.append(str(container))
        if tag is not None:
            full_cmd.append(tag)

        return python_on_whales.components.image.Image(
            self.client_config, run(full_cmd), is_immutable_id=True
        )

    def copy(
        self,
        source: Union[ValidPath, ContainerPath],
        destination: Union[ValidPath, ContainerPath],
    ):
        """Copy files/folders between a container and the local filesystem

        Alias: `docker.copy(...)`

        ```python
        from python_on_whales import docker

        docker.run("ubuntu", ["sleep", "infinity"], name="dodo", remove=True, detach=True)

        docker.copy("/tmp/my_local_file.txt", ("dodo", "/path/in/container.txt"))
        docker.copy(("dodo", "/path/in/container.txt"), "/tmp/my_local_file2.txt")
        ```

        Doesn't yet support sending or receiving iterators of Python bytes.

        # Arguments
            source: Local path or tuple. When using a tuple, the first element
                of the tuple is the container, the second element is the path in
                the container. ex: `source=("my-container", "/usr/bin/something")`.
            destination: Local path or tuple. When using a tuple, the first element
                of the tuple is the container, the second element is the path in
                the container. ex: `source=("my-container", "/usr/bin/something")`.
        """
        # TODO: tests and handling bytes streams.
        full_cmd = self.docker_cmd + ["container", "cp"]

        if isinstance(source, bytes) or inspect.isgenerator(source):
            source = "-"
        elif isinstance(source, tuple):
            source = f"{str(source[0])}:{source[1]}"
        else:
            source = str(source)

        if destination is None:
            destination = "-"
        elif isinstance(destination, tuple):
            destination = f"{str(destination[0])}:{destination[1]}"
        else:
            destination = str(destination)

        run(full_cmd + [source, destination])

    def create(
        self,
        image: str,
        command: List[str] = [],
        *,
        add_hosts: List[Tuple[str, str]] = [],
        blkio_weight: Optional[int] = None,
        blkio_weight_device: List[str] = [],
        cap_add: List[str] = [],
        cap_drop: List[str] = [],
        cgroup_parent: Optional[str] = None,
        cidfile: Optional[ValidPath] = None,
        cpu_period: Optional[int] = None,
        cpu_quota: Optional[int] = None,
        cpu_rt_period: Optional[int] = None,
        cpu_rt_runtime: Optional[int] = None,
        cpu_shares: Optional[int] = None,
        cpus: Optional[float] = None,
        cpuset_cpus: Optional[List[int]] = None,
        cpuset_mems: Optional[List[int]] = None,
        detach: bool = False,
        devices: List[str] = [],
        device_cgroup_rules: List[str] = [],
        device_read_bps: List[str] = [],
        device_read_iops: List[str] = [],
        device_write_bps: List[str] = [],
        device_write_iops: List[str] = [],
        content_trust: bool = False,
        dns: List[str] = [],
        dns_options: List[str] = [],
        dns_search: List[str] = [],
        domainname: Optional[str] = None,
        entrypoint: Optional[str] = None,
        envs: Dict[str, str] = {},
        env_files: Union[ValidPath, List[ValidPath]] = [],
        expose: Union[int, List[int]] = [],
        gpus: Union[int, str, None] = None,
        groups_add: List[str] = [],
        healthcheck: bool = True,
        health_cmd: Optional[str] = None,
        health_interval: Union[None, int, timedelta] = None,
        health_retries: Optional[int] = None,
        health_start_period: Union[None, int, timedelta] = None,
        health_timeout: Union[None, int, timedelta] = None,
        hostname: Optional[str] = None,
        init: bool = False,
        ip: Optional[str] = None,
        ip6: Optional[str] = None,
        ipc: Optional[str] = None,
        isolation: Optional[str] = None,
        kernel_memory: Union[int, str, None] = None,
        labels: Dict[str, str] = {},
        label_files: List[ValidPath] = [],
        link: List[ValidContainer] = [],
        link_local_ip: List[str] = [],
        log_driver: Optional[str] = None,
        log_options: List[str] = [],
        mac_address: Optional[str] = None,
        memory: Union[int, str, None] = None,
        memory_reservation: Union[int, str, None] = None,
        memory_swap: Union[int, str, None] = None,
        memory_swappiness: Optional[int] = None,
        mounts: List[List[str]] = [],
        name: Optional[str] = None,
        networks: List[python_on_whales.components.network.ValidNetwork] = [],
        network_aliases: List[str] = [],
        oom_kill: bool = True,
        oom_score_adj: Optional[int] = None,
        pid: Optional[str] = None,
        pids_limit: Optional[int] = None,
        platform: Optional[str] = None,
        privileged: bool = False,
        publish: List[ValidPortMapping] = [],
        publish_all: bool = False,
        read_only: bool = False,
        restart: Optional[str] = None,
        remove: bool = False,
        runtime: Optional[str] = None,
        security_options: List[str] = [],
        shm_size: Union[int, str, None] = None,
        sig_proxy: bool = True,
        stop_signal: Optional[str] = None,
        stop_timeout: Optional[int] = None,
        storage_options: List[str] = [],
        sysctl: Dict[str, str] = {},
        tmpfs: List[ValidPath] = [],
        ulimit: List[str] = [],
        user: Optional[str] = None,
        userns: Optional[str] = None,
        uts: Optional[str] = None,
        volumes: Optional[
            List[python_on_whales.components.volume.VolumeDefinition]
        ] = [],
        volume_driver: Optional[str] = None,
        volumes_from: List[ValidContainer] = [],
        workdir: Optional[ValidPath] = None,
    ) -> Container:
        """Creates a container, but does not start it.

        Alias: `docker.create(...)`

        Start it then with the `.start()` method.

        It might be useful if you want to delay the start of a container,
        to do some preparations beforehand. For example, it's common to do this
        workflow: `docker create` -> `docker cp` -> `docker start` to put files
        in the container before starting.

        There is no `detach` argument since it's a runtime option.

        The arguments are the same as [`docker.run`](#run).
        """
        python_on_whales.components.image.ImageCLI(
            self.client_config
        )._pull_if_necessary(image)
        full_cmd = self.docker_cmd + ["create"]

        add_hosts = [f"{host}:{ip}" for host, ip in add_hosts]
        full_cmd.add_args_list("--add-host", add_hosts)

        full_cmd.add_simple_arg("--blkio-weight", blkio_weight)
        full_cmd.add_args_list("--blkio-weight-device", blkio_weight_device)

        full_cmd.add_args_list("--cap-add", cap_add)
        full_cmd.add_args_list("--cap-drop", cap_drop)

        full_cmd.add_simple_arg("--cgroup-parent", cgroup_parent)
        full_cmd.add_simple_arg("--cidfile", cidfile)

        full_cmd.add_simple_arg("--cpu-period", cpu_period)
        full_cmd.add_simple_arg("--cpu-quota", cpu_quota)
        full_cmd.add_simple_arg("--cpu-rt-period", cpu_rt_period)
        full_cmd.add_simple_arg("--cpu-rt-runtime", cpu_rt_runtime)
        full_cmd.add_simple_arg("--cpu-shares", cpu_shares)
        full_cmd.add_simple_arg("--cpus", cpus)
        full_cmd.add_simple_arg("--cpuset-cpus", join_if_not_none(cpuset_cpus))
        full_cmd.add_simple_arg("--cpuset-mems", join_if_not_none(cpuset_mems))

        full_cmd.add_flag("--detach", detach)

        full_cmd.add_args_list("--device", devices)
        full_cmd.add_args_list("--device-cgroup-rule", device_cgroup_rules)
        full_cmd.add_args_list("--device-read-bps", device_read_bps)
        full_cmd.add_args_list("--device-read-iops", device_read_iops)
        full_cmd.add_args_list("--device-write-bps", device_write_bps)
        full_cmd.add_args_list("--device-write-iops", device_write_iops)

        if content_trust:
            full_cmd += ["--disable-content-trust", "false"]

        full_cmd.add_args_list("--dns", dns)
        full_cmd.add_args_list("--dns-option", dns_options)
        full_cmd.add_args_list("--dns-search", dns_search)
        full_cmd.add_simple_arg("--domainname", domainname)

        full_cmd.add_simple_arg("--entrypoint", entrypoint)

        full_cmd.add_args_list("--env", format_dict_for_cli(envs))
        full_cmd.add_args_list("--env-file", env_files)

        full_cmd.add_args_list("--expose", expose)

        full_cmd.add_simple_arg("--gpus", gpus)

        full_cmd.add_args_list("--group-add", groups_add)

        full_cmd.add_flag("--no-healthcheck", not healthcheck)
        full_cmd.add_simple_arg("--health-cmd", health_cmd)
        full_cmd.add_simple_arg("--health-interval", to_seconds(health_interval))
        full_cmd.add_simple_arg("--health-retries", health_retries)
        full_cmd.add_simple_arg(
            "--health-start-period", to_seconds(health_start_period)
        )
        full_cmd.add_simple_arg("--health-timeout", to_seconds(health_timeout))

        full_cmd.add_simple_arg("--hostname", hostname)

        full_cmd.add_flag("--init", init)

        full_cmd.add_simple_arg("--ip", ip)
        full_cmd.add_simple_arg("--ip6", ip6)
        full_cmd.add_simple_arg("--ipc", ipc)

        full_cmd.add_simple_arg("--isolation", isolation)
        full_cmd.add_simple_arg("--kernel-memory", kernel_memory)

        full_cmd.add_args_list("--label", format_dict_for_cli(labels))
        full_cmd.add_args_list("--label-file", label_files)

        full_cmd.add_args_list("--link", link)
        full_cmd.add_args_list("--link-local-ip", link_local_ip)

        full_cmd.add_simple_arg("--log-driver", log_driver)
        full_cmd.add_args_list("--log-opt", log_options)

        full_cmd.add_simple_arg("--mac-address", mac_address)

        full_cmd.add_simple_arg("--memory", memory)
        full_cmd.add_simple_arg("--memory-reservation", memory_reservation)
        full_cmd.add_simple_arg("--memory-swap", memory_swap)
        full_cmd.add_simple_arg("--memory-swappiness", memory_swappiness)

        mounts = [",".join(x) for x in mounts]
        full_cmd.add_args_list("--mount", mounts)
        full_cmd.add_simple_arg("--name", name)

        full_cmd.add_args_list("--network", networks)
        full_cmd.add_args_list("--network-aliases", network_aliases)

        full_cmd.add_flag("--oom-kill-disable", not oom_kill)
        full_cmd.add_simple_arg("--oom-score-adj", oom_score_adj)

        full_cmd.add_simple_arg("--pid", pid)
        full_cmd.add_simple_arg("--pids-limit", pids_limit)

        full_cmd.add_simple_arg("--platform", platform)
        full_cmd.add_flag("--privileged", privileged)

        for port_mapping in publish:
            if len(port_mapping) == 2:
                full_cmd += ["-p", f"{port_mapping[0]}:{port_mapping[1]}"]
            else:
                full_cmd += [
                    "-p",
                    f"{port_mapping[0]}:{port_mapping[1]}/{port_mapping[2]}",
                ]
        full_cmd.add_flag("--publish-all", publish_all)

        full_cmd.add_flag("--read-only", read_only)
        full_cmd.add_simple_arg("--restart", restart)
        full_cmd.add_flag("--rm", remove)

        full_cmd.add_simple_arg("--runtime", runtime)
        full_cmd.add_args_list("--security-opt", security_options)

        full_cmd.add_simple_arg("--shm-size", shm_size)
        if sig_proxy is False:
            full_cmd += ["--sig-proxy", "false"]

        full_cmd.add_simple_arg("--stop-signal", stop_signal)
        full_cmd.add_simple_arg("--stop-timeout", stop_timeout)

        full_cmd.add_args_list("--storage-opt", storage_options)
        full_cmd.add_args_list("--sysctl", format_dict_for_cli(sysctl))
        full_cmd.add_args_list("--tmpfs", tmpfs)
        full_cmd.add_args_list("--ulimit", ulimit)

        full_cmd.add_simple_arg("--user", user)
        full_cmd.add_simple_arg("--userns", userns)
        full_cmd.add_simple_arg("--uts", uts)

        for volume_definition in volumes:
            volume_definition = tuple(str(x) for x in volume_definition)
            full_cmd += ["--volume", ":".join(volume_definition)]
        full_cmd.add_simple_arg("--volume-driver", volume_driver)
        full_cmd.add_args_list("--volumes-from", volumes_from)

        full_cmd.add_simple_arg("--workdir", workdir)

        full_cmd.append(image)
        full_cmd += command
        return Container(self.client_config, run(full_cmd), is_immutable_id=True)

    def diff(self, container: ValidContainer) -> Dict[str, str]:
        """List all the files modified, added or deleted since the container started.

        Alias: `docker.diff(...)`

        # Arguments
            container: The container to inspect

        # Returns
            `Dict[str, str]` Something like
            `{"/some_path": "A", "/some_file": "M", "/tmp": "D"}` for example.

        """
        full_cmd = self.docker_cmd + ["diff", container]

        result_dict = {}
        result = run(full_cmd)
        for line in result.splitlines():
            result_dict[line[2:]] = line[0]
        return result_dict

    def execute(
        self,
        container: ValidContainer,
        command: Union[str, List[str]],
        detach: bool = False,
    ) -> Optional[str]:
        """Execute a command inside a container

        Alias: `docker.execute(...)`

        # Arguments
            container: The container to execute the command in.
            command: The command to execute.
            detach: if `True`, returns immediately with `None`. If `False`,
                returns the command stdout as string.

        # Returns:
            Optional[str]
        """
        full_cmd = self.docker_cmd + ["exec"]

        full_cmd.add_flag("--detach", detach)

        full_cmd.append(container)
        for arg in to_list(command):
            full_cmd.append(arg)

        result = run(full_cmd)
        if detach:
            return None
        else:
            return result

    def export(self, container: ValidContainer, output: ValidPath) -> None:
        """Export a container's filesystem as a tar archive

        Alias: `docker.export(...)`

        # Arguments
            container: The container to export.
            output: The path of the output tar archive.
        """
        full_cmd = self.docker_cmd + [
            "container",
            "--output",
            output,
            "export",
            container,
        ]
        run(full_cmd)

    @overload
    def inspect(self, x: str) -> Container:
        ...

    @overload
    def inspect(self, x: List[str]) -> List[Container]:
        ...

    def inspect(self, x: Union[str, List[str]]) -> Union[Container, List[Container]]:
        """Returns a container object from a name or ID.

        # Arguments
            reference: A container name or ID, or a list of container names
                and/or IDs

        # Returns:
            A `python_on_whales.Container` object or a list of those
            if a list of IDs was passed as input.
        """
        if isinstance(x, list):
            return [Container(self.client_config, reference) for reference in x]
        else:
            return Container(self.client_config, x)

    def kill(
        self,
        containers: Union[ValidContainer, List[ValidContainer]],
        signal: str = None,
    ):
        """Kill a container.

        Alias: `docker.kill(...)`

        # Arguments
            containers: One or more containers to kill
            signal: The signal to send the container
        """
        full_cmd = self.docker_cmd + ["container", "kill"]

        full_cmd.add_simple_arg("--signal", signal)

        for container in to_list(containers):
            full_cmd.append(container)

        run(full_cmd)

    def logs(
        self,
        container: Union[Container, str],
        details: bool = False,
        since: Union[None, datetime, timedelta] = None,
        tail: Optional[int] = None,
        timestamps: bool = False,
        until: Union[None, datetime, timedelta] = None,
    ) -> str:
        """Returns the logs of a container as a string.

        Alias: `docker.logs(...)`

        The follow option is not yet implemented.

        # Arguments
            container: The container to get the logs of
            details: Show extra details provided to logs
            since: Use a datetime or timedelta to specify the lower
                date limit for the logs.
            tail: Number of lines to show from the end of the logs (default all)
            timestamps: Put timestamps next to lines.
            until: Use a datetime or a timedelta to specify the upper date
                limit for the logs.

        # Returns
            `str`
        """
        full_cmd = self.docker_cmd + ["container", "logs"]
        full_cmd.add_flag("--details", details)
        full_cmd.add_simple_arg("--since", format_time_arg(since))
        full_cmd.add_simple_arg("--tail", tail)
        full_cmd.add_flag("--timestamps", timestamps)
        full_cmd.add_simple_arg("--until", format_time_arg(until))
        return run(full_cmd + [container])

    def list(self, all: bool = False, filters: Dict[str, str] = {}) -> List[Container]:
        """List the containers on the host.

        Alias: `docker.ps(...)`

        # Arguments
            all: If `True`, also returns containers that are not running.

        # Returns
            A `List[python_on_whales.Container]`
        """
        full_cmd = self.docker_cmd
        full_cmd += ["container", "list", "-q", "--no-trunc"]
        full_cmd.add_args_list("--filter", format_dict_for_cli(filters))
        full_cmd.add_flag("--all", all)

        # TODO: add a test for the fix of is_immutable_id, without it, we get
        # race conditions (we read the attributes of a container but it might not exist.
        return [
            Container(self.client_config, x, is_immutable_id=True)
            for x in run(full_cmd).splitlines()
        ]

    def pause(self, containers: Union[ValidContainer, List[ValidContainer]]):
        """Pauses one or more containers

        Alias: `docker.pause(...)`

        # Arguments
            containers: One or more containers to pause
        """
        full_cmd = self.docker_cmd + ["pause"]
        for container in to_list(containers):
            full_cmd.append(str(container))

        run(full_cmd)

    def prune(self, filters: Union[str, List[str]] = []) -> None:
        """Remove containers that are not running.

        # Arguments
            filters: Filters as strings or list of strings
        """
        full_cmd = self.docker_cmd + ["container", "prune", "--force"]
        for filter_ in to_list(filters):
            full_cmd += ["--filter", filter_]
        run(full_cmd)

    def rename(self, container: ValidContainer, new_name: str) -> None:
        """Changes the name of a container.

        Alias: `docker.rename(...)`

        # Arguments
            container: The container to rename
            new_name: The new name of the container.
        """
        full_cmd = self.docker_cmd + ["container", "rename", str(container), new_name]
        run(full_cmd)

    def restart(
        self,
        containers: Union[ValidContainer, List[ValidContainer]],
        time: Optional[Union[int, timedelta]] = None,
    ):
        """Restarts one or more container.

        Alias: `docker.restart(...)`

        # Arguments
            containers: One or more containers to restart
            time: Amount of to wait for stop before killing the container (default 10s).
                If `int`, the unit is seconds.
        """
        full_cmd = self.docker_cmd + ["restart"]

        if time is not None:
            if isinstance(time, timedelta):
                time = time.total_seconds()
            full_cmd += ["--time", str(time)]

        for container in to_list(containers):
            full_cmd.append(str(container))

        run(full_cmd)

    def remove(
        self,
        containers: Union[Container, str, List[Union[Container, str]]],
        force: bool = False,
        volumes: bool = False,
    ) -> None:
        """Removes a container

        Alias: `docker.remove(...)`

        # Arguments
            containers: One or more containers.
            force: Force the removal of a running container (uses SIGKILL)
            volumes: Remove anonymous volumes associated with the container
        """
        full_cmd = self.docker_cmd + ["container", "rm"]
        full_cmd.add_flag("--force", force)
        full_cmd.add_flag("--volumes", volumes)

        for container in to_list(containers):
            full_cmd.append(str(container))

        run(full_cmd)

    def run(
        self,
        image: python_on_whales.components.image.ValidImage,
        command: List[str] = [],
        *,
        add_hosts: List[Tuple[str, str]] = [],
        blkio_weight: Optional[int] = None,
        blkio_weight_device: List[str] = [],
        cap_add: List[str] = [],
        cap_drop: List[str] = [],
        cgroup_parent: Optional[str] = None,
        cidfile: Optional[ValidPath] = None,
        cpu_period: Optional[int] = None,
        cpu_quota: Optional[int] = None,
        cpu_rt_period: Optional[int] = None,
        cpu_rt_runtime: Optional[int] = None,
        cpu_shares: Optional[int] = None,
        cpus: Optional[float] = None,
        cpuset_cpus: Optional[List[int]] = None,
        cpuset_mems: Optional[List[int]] = None,
        detach: bool = False,
        devices: List[str] = [],
        device_cgroup_rules: List[str] = [],
        device_read_bps: List[str] = [],
        device_read_iops: List[str] = [],
        device_write_bps: List[str] = [],
        device_write_iops: List[str] = [],
        content_trust: bool = False,
        dns: List[str] = [],
        dns_options: List[str] = [],
        dns_search: List[str] = [],
        domainname: Optional[str] = None,
        entrypoint: Optional[str] = None,
        envs: Dict[str, str] = {},
        env_files: Union[ValidPath, List[ValidPath]] = [],
        expose: Union[int, List[int]] = [],
        gpus: Union[int, str, None] = None,
        groups_add: List[str] = [],
        healthcheck: bool = True,
        health_cmd: Optional[str] = None,
        health_interval: Union[None, int, timedelta] = None,
        health_retries: Optional[int] = None,
        health_start_period: Union[None, int, timedelta] = None,
        health_timeout: Union[None, int, timedelta] = None,
        hostname: Optional[str] = None,
        init: bool = False,
        ip: Optional[str] = None,
        ip6: Optional[str] = None,
        ipc: Optional[str] = None,
        isolation: Optional[str] = None,
        kernel_memory: Union[int, str, None] = None,
        labels: Dict[str, str] = {},
        label_files: List[ValidPath] = [],
        link: List[ValidContainer] = [],
        link_local_ip: List[str] = [],
        log_driver: Optional[str] = None,
        log_options: List[str] = [],
        mac_address: Optional[str] = None,
        memory: Union[int, str, None] = None,
        memory_reservation: Union[int, str, None] = None,
        memory_swap: Union[int, str, None] = None,
        memory_swappiness: Optional[int] = None,
        mounts: List[List[str]] = [],
        name: Optional[str] = None,
        networks: List[python_on_whales.components.network.ValidNetwork] = [],
        network_aliases: List[str] = [],
        oom_kill: bool = True,
        oom_score_adj: Optional[int] = None,
        pid: Optional[str] = None,
        pids_limit: Optional[int] = None,
        platform: Optional[str] = None,
        privileged: bool = False,
        publish: List[ValidPortMapping] = [],
        publish_all: bool = False,
        read_only: bool = False,
        restart: Optional[str] = None,
        remove: bool = False,
        runtime: Optional[str] = None,
        security_options: List[str] = [],
        shm_size: Union[int, str, None] = None,
        sig_proxy: bool = True,
        stop_signal: Optional[str] = None,
        stop_timeout: Optional[int] = None,
        storage_options: List[str] = [],
        stream: bool = False,
        sysctl: Dict[str, str] = {},
        tmpfs: List[ValidPath] = [],
        ulimit: List[str] = [],
        user: Optional[str] = None,
        userns: Optional[str] = None,
        uts: Optional[str] = None,
        volumes: Optional[
            List[python_on_whales.components.volume.VolumeDefinition]
        ] = [],
        volume_driver: Optional[str] = None,
        volumes_from: List[ValidContainer] = [],
        workdir: Optional[ValidPath] = None,
    ) -> Union[Container, str, Iterable[Tuple[str, bytes]]]:
        """Runs a container

        You can use `docker.run` or `docker.container.run` to call this function.

        For a deeper dive into the arguments and what they do, visit
        <https://docs.docker.com/engine/reference/run/>

        If you want to know exactly how to call `docker.run()` depending on your
        use case (detach, stream...), take a look at
        the [`docker.run()` guide](../user_guide/docker_run.md).

        ```python
        >>> from python_on_whales import docker
        >>> returned_string = docker.run("hello-world")
        >>> print(returned_string)

        Hello from Docker!
        This message shows that your installation appears to be working correctly.

        To generate this message, Docker took the following steps:
         1. The Docker client contacted the Docker daemon.
         2. The Docker daemon pulled the "hello-world" image from the Docker Hub.
            (amd64)
         3. The Docker daemon created a new container from that image which runs the
            executable that produces the output you are currently reading.
         4. The Docker daemon streamed that output to the Docker client, which sent it
            to your terminal.

        To try something more ambitious, you can run an Ubuntu container with:
         $ docker run -it ubuntu bash

        Share images, automate workflows, and more with a free Docker ID:
         https://hub.docker.com/

        For more examples and ideas, visit:
         https://docs.docker.com/get-started/
        ```

        ```python
        >>> from python_on_whales import docker
        >>> result_string = docker.run("ubuntu", ["ls", "/host"], volumes=[("/", "/host", "ro")])
        >>> print(result_string)
        bin
        boot
        dev
        etc
        home
        init
        lib
        lib64
        lost+found
        media
        mnt
        opt
        proc
        projects
        root
        run
        sbin
        snap
        srv
        sys
        tmp
        usr
        var
        ```

        # Arguments
            image: The docker image to use for the container
            command: List of arguments to provide to the container.
            add_hosts: hosts to add in the format of a tuple. For example,
                `add_hosts=[("my_host_1", "192.168.30.31"), ("host2", "192.168.80.81")]`
            blkio_weight: Block IO (relative weight), between 10 and 1000,
                or 0 to disable (default 0)
            cpu_period: Limit CPU CFS (Completely Fair Scheduler) period
            cpu_quota: Limit CPU CFS (Completely Fair Scheduler) quota
            cpu_rt_period: Limit CPU real-time period in microseconds
            cpu_rt_runtime: Limit CPU real-time runtime in microseconds
            cpu_shares: CPU shares (relative weight)
            cpus: The maximal amount of cpu the container can use.
                `1` means one cpu core.
            cpuset_cpus: CPUs in which to allow execution. Must be given as a list.
            cpuset_mems: MEMs in which to allow execution. Must be given as a list.
            detach: If `False`, returns the ouput of the container as a string.
                If `True`, returns a `python_on_whales.Container` object.
            dns_search: Set custom DNS search domains
            domainname: Container NIS domain name
            entrypoint: Overwrite the default ENTRYPOINT of the image
            envs: Environment variables as a `dict`.
                For example: `{"OMP_NUM_THREADS": 3}`
            env_files: One or a list of env files.
            gpus: For this to work, you need the
                [Nvidia container runtime](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html#install-guide)
                The value needed is a `str` or `int`. Some examples of valid argument
                are `"all"` or `"device=GPU-3a23c669-1f69-c64e-cf85-44e9b07e7a2a"` or
                `"device=0,2"`. If you want 3 gpus, just write `gpus=3`.
            hostname: Container host name
            ip: IPv4 address (e.g., 172.30.100.104)
            ip6: IPv6 address (e.g., 2001:db8::33)
            ipc: IPC mode to use
            isolation: Container isolation technology
            kernel_memory: Kernel memory limit. `int` represents the number of bytes,
                but you can use `"4k"` or `2g` for example.
            log_driver: Logging driver for the container
            mac_adress: Container MAC address (e.g., `"92:d0:c6:0a:29:33"`)
            memory:  Memory limit, valid values are `1024` (ints are bytes) or
                `"43m"` or `"6g"`.
            memory_reservation: Memory soft limit
            memory_swap: Swap limit equal to memory plus swap: '-1'
                to enable unlimited swap.
            memory_swappiness: Tune container memory swappiness (0 to 100) (default -1)
            name: The container name. If not provided, one is automatically genrated for
                you.
            healthcheck: Set to `False` to disable container periodic healthcheck.
            oom_kill: Set to `False` to disable the OOM killer for this container.
            pid: PID namespace to use
            pids_limit: Tune container pids limit (set `-1` for unlimited)
            platform: Set platform if server is multi-platform capable.
            privileged: Give extended privileges to this container.
            publish: Ports to publish, same as the `-p` argument in the Docker CLI.
                example are `[(8000, 7000) , ("127.0.0.1:3000", 2000)]` or
                `[("127.0.0.1:3000", 2000, "udp")]`.
            publish_all: Publish all exposed ports to random ports.
            read_only: Mount the container's root filesystem as read only.
            restart: Restart policy to apply when a container exits (default "no")
            remove: Automatically remove the container when it exits.
            runtime: Runtime to use for this container.
            security_options: Security options
            shm_size: Size of /dev/shm. `int` is for bytes. But you can use `"512m"` or
                `"4g"` for example.
            stop_timeout: Signal to stop a container (default "SIGTERM")
            storage_options: Storage driver options for the container
            user: Username or UID (format: `<name|uid>[:<group|gid>]`)
            userns:  User namespace to use
            uts:  UTS namespace to use
            volumes:  Bind mount a volume. Some examples:
                `[("/", "/host"), ("/etc/hosts", "/etc/hosts", "rw")]`.
            volume_driver: Optional volume driver for the container
            workdir: The directory in the container where the process will be executed.

        # Returns
            The container output as a string if detach is `False` (the default),
            and a `python_on_whales.Container` if detach is `True`.
        """

        python_on_whales.components.image.ImageCLI(
            self.client_config
        )._pull_if_necessary(image)

        full_cmd = self.docker_cmd + ["container", "run"]

        add_hosts = [f"{host}:{ip}" for host, ip in add_hosts]
        full_cmd.add_args_list("--add-host", add_hosts)

        full_cmd.add_simple_arg("--blkio-weight", blkio_weight)
        full_cmd.add_args_list("--blkio-weight-device", blkio_weight_device)

        full_cmd.add_args_list("--cap-add", cap_add)
        full_cmd.add_args_list("--cap-drop", cap_drop)

        full_cmd.add_simple_arg("--cgroup-parent", cgroup_parent)
        full_cmd.add_simple_arg("--cidfile", cidfile)

        full_cmd.add_simple_arg("--cpu-period", cpu_period)
        full_cmd.add_simple_arg("--cpu-quota", cpu_quota)
        full_cmd.add_simple_arg("--cpu-rt-period", cpu_rt_period)
        full_cmd.add_simple_arg("--cpu-rt-runtime", cpu_rt_runtime)
        full_cmd.add_simple_arg("--cpu-shares", cpu_shares)
        full_cmd.add_simple_arg("--cpus", cpus)
        full_cmd.add_simple_arg("--cpuset-cpus", join_if_not_none(cpuset_cpus))
        full_cmd.add_simple_arg("--cpuset-mems", join_if_not_none(cpuset_mems))

        full_cmd.add_flag("--detach", detach)

        full_cmd.add_args_list("--device", devices)
        full_cmd.add_args_list("--device-cgroup-rule", device_cgroup_rules)
        full_cmd.add_args_list("--device-read-bps", device_read_bps)
        full_cmd.add_args_list("--device-read-iops", device_read_iops)
        full_cmd.add_args_list("--device-write-bps", device_write_bps)
        full_cmd.add_args_list("--device-write-iops", device_write_iops)

        if content_trust:
            full_cmd += ["--disable-content-trust", "false"]

        full_cmd.add_args_list("--dns", dns)
        full_cmd.add_args_list("--dns-option", dns_options)
        full_cmd.add_args_list("--dns-search", dns_search)
        full_cmd.add_simple_arg("--domainname", domainname)

        full_cmd.add_simple_arg("--entrypoint", entrypoint)

        full_cmd.add_args_list("--env", format_dict_for_cli(envs))
        full_cmd.add_args_list("--env-file", env_files)

        full_cmd.add_args_list("--expose", expose)

        full_cmd.add_simple_arg("--gpus", gpus)

        full_cmd.add_args_list("--group-add", groups_add)

        full_cmd.add_flag("--no-healthcheck", not healthcheck)
        full_cmd.add_simple_arg("--health-cmd", health_cmd)
        full_cmd.add_simple_arg("--health-interval", to_seconds(health_interval))
        full_cmd.add_simple_arg("--health-retries", health_retries)
        full_cmd.add_simple_arg(
            "--health-start-period", to_seconds(health_start_period)
        )
        full_cmd.add_simple_arg("--health-timeout", to_seconds(health_timeout))

        full_cmd.add_simple_arg("--hostname", hostname)

        full_cmd.add_flag("--init", init)

        full_cmd.add_simple_arg("--ip", ip)
        full_cmd.add_simple_arg("--ip6", ip6)
        full_cmd.add_simple_arg("--ipc", ipc)

        full_cmd.add_simple_arg("--isolation", isolation)
        full_cmd.add_simple_arg("--kernel-memory", kernel_memory)

        full_cmd.add_args_list("--label", format_dict_for_cli(labels))
        full_cmd.add_args_list("--label-file", label_files)

        full_cmd.add_args_list("--link", link)
        full_cmd.add_args_list("--link-local-ip", link_local_ip)

        full_cmd.add_simple_arg("--log-driver", log_driver)
        full_cmd.add_args_list("--log-opt", log_options)

        full_cmd.add_simple_arg("--mac-address", mac_address)

        full_cmd.add_simple_arg("--memory", memory)
        full_cmd.add_simple_arg("--memory-reservation", memory_reservation)
        full_cmd.add_simple_arg("--memory-swap", memory_swap)
        full_cmd.add_simple_arg("--memory-swappiness", memory_swappiness)

        mounts = [",".join(x) for x in mounts]
        full_cmd.add_args_list("--mount", mounts)
        full_cmd.add_simple_arg("--name", name)

        full_cmd.add_args_list("--network", networks)
        full_cmd.add_args_list("--network-aliases", network_aliases)

        full_cmd.add_flag("--oom-kill-disable", not oom_kill)
        full_cmd.add_simple_arg("--oom-score-adj", oom_score_adj)

        full_cmd.add_simple_arg("--pid", pid)
        full_cmd.add_simple_arg("--pids-limit", pids_limit)

        full_cmd.add_simple_arg("--platform", platform)
        full_cmd.add_flag("--privileged", privileged)

        for port_mapping in publish:
            if len(port_mapping) == 2:
                full_cmd += ["-p", f"{port_mapping[0]}:{port_mapping[1]}"]
            else:
                full_cmd += [
                    "-p",
                    f"{port_mapping[0]}:{port_mapping[1]}/{port_mapping[2]}",
                ]
        full_cmd.add_flag("--publish-all", publish_all)

        full_cmd.add_flag("--read-only", read_only)
        full_cmd.add_simple_arg("--restart", restart)
        full_cmd.add_flag("--rm", remove)

        full_cmd.add_simple_arg("--runtime", runtime)
        full_cmd.add_args_list("--security-opt", security_options)

        full_cmd.add_simple_arg("--shm-size", shm_size)
        if sig_proxy is False:
            full_cmd += ["--sig-proxy", "false"]

        full_cmd.add_simple_arg("--stop-signal", stop_signal)
        full_cmd.add_simple_arg("--stop-timeout", stop_timeout)

        full_cmd.add_args_list("--storage-opt", storage_options)
        full_cmd.add_args_list("--sysctl", format_dict_for_cli(sysctl))
        full_cmd.add_args_list("--tmpfs", tmpfs)
        full_cmd.add_args_list("--ulimit", ulimit)

        full_cmd.add_simple_arg("--user", user)
        full_cmd.add_simple_arg("--userns", userns)
        full_cmd.add_simple_arg("--uts", uts)

        for volume_definition in volumes:
            volume_definition = tuple(str(x) for x in volume_definition)
            full_cmd += ["--volume", ":".join(volume_definition)]
        full_cmd.add_simple_arg("--volume-driver", volume_driver)
        full_cmd.add_args_list("--volumes-from", volumes_from)

        full_cmd.add_simple_arg("--workdir", workdir)

        full_cmd.append(image)
        full_cmd += command

        if detach and stream:
            raise ValueError(
                "It's not possible to stream and detach a container at "
                "the same time."
            )
        if detach:
            return Container(self.client_config, run(full_cmd))
        elif stream:
            return stream_stdout_and_stderr(full_cmd)
        else:
            return run(full_cmd, capture_stderr=False)

    def start(
        self,
        containers: Union[ValidContainer, List[ValidContainer]],
        attach: bool = False,
        stream: bool = False,
    ) -> Union[None, str, Iterable[Tuple[str, bytes]]]:
        """Starts one or more stopped containers.

        Aliases: `docker.start`, `docker.container.start`,
        `python_on_whales.Container.start`.

        # Arguments
            containers: One or a list of containers.
        """
        if attach and isinstance(containers, list):
            raise ValueError("Attaching multiple containers on start is not supported.")
        if not attach and stream:
            raise ValueError(
                "It's not possible to stream stderr and stdout if the client isn't "
                "attached to the container. Please set `attach=True`."
            )
        full_cmd = self.docker_cmd + ["container", "start"]
        full_cmd.add_flag("--attach", attach)
        full_cmd += to_list(containers)

        if stream:
            return stream_stdout_and_stderr(full_cmd)
        elif attach:
            return run(full_cmd)
        else:
            run(full_cmd)

    def stats(self, all: bool = False) -> List[ContainerStats]:
        """Get containers resource usage statistics

        Alias: `docker.stats(...)`

        Usage:
        ```python
        from python_on_whales import docker

        docker.run("redis", detach=True)
        print(docker.stats())
        # [<<class 'python_on_whales.components.container.ContainerStats'> object,
        # attributes are block_read=0, block_write=0, cpu_percentage=0.08,
        # container=e90ae41a5b17,
        # container_id=e90ae41a5b17df998584141692f1e361c485e8d00c37ee21fdc360d3523dd1c1,
        # memory_percentage=0.18, memory_used=11198791, memory_limit=6233071288,
        # container_name=crazy_northcutt, net_upload=696, net_download=0>]
        ```

        The data unit is the byte.

        # Arguments
            all: Get the stats of all containers, not just running ones.

        # Returns
            A `List[python_on_whales.ContainerStats]`.
        """
        full_cmd = self.docker_cmd + [
            "container",
            "stats",
            "--format",
            "{{json .}}",
            "--no-stream",
            "--no-trunc",
        ]
        full_cmd.add_flag("--all", all)
        stats_output = run(full_cmd)
        return [ContainerStats(json.loads(x)) for x in stats_output.splitlines()]

    def stop(
        self,
        containers: Union[ValidContainer, List[ValidContainer]],
        time: Union[int, timedelta] = None,
    ):
        """Stops one or more running containers

        Alias: `docker.stop(...)`

        Aliases: `docker.stop`, `docker.container.stop`,
        `python_on_whales.Container.stop`.

        # Arguments
            containers: One or a list of containers.
            time: Seconds to wait for stop before killing a container (default 10)
        """
        full_cmd = self.docker_cmd + ["container", "stop"]
        if isinstance(time, timedelta):
            time = time.total_seconds()

        if time is not None:
            full_cmd += ["--time", str(time)]

        for container in to_list(containers):
            full_cmd.append(container)

        run(full_cmd)

    def top(self):
        """Get the running processes of a container

        Alias: `docker.top(...)`

        Not yet implemented"""
        raise NotImplementedError

    def unpause(self, x: Union[ValidContainer, List[ValidContainer]]):
        """Unpause all processes within one or more containers

        Alias: `docker.unpause(...)`

        # Arguments
            x: One or more containers (name, id or `python_on_whales.Container` object).
        """
        full_cmd = self.docker_cmd + ["container", "unpause"]
        full_cmd += to_list(x)
        run(full_cmd)

    def update(
        self,
        x: Union[ValidContainer, List[ValidContainer]],
        blkio_weight: Optional[int] = None,
        cpu_period: Optional[int] = None,
        cpu_quota: Optional[int] = None,
        cpu_rt_period: Optional[int] = None,
        cpu_rt_runtime: Optional[int] = None,
        cpu_shares: Optional[int] = None,
        cpus: Optional[float] = None,
        cpuset_cpus: Optional[List[int]] = None,
        cpuset_mems: Optional[List[int]] = None,
        kernel_memory: Union[int, str, None] = None,
        memory: Union[int, str, None] = None,
        memory_reservation: Union[int, str, None] = None,
        memory_swap: Union[int, str, None] = None,
        pids_limit: Optional[int] = None,
        restart: Optional[str] = None,
    ):
        """Update configuration of one or more containers

        Alias: `docker.update(...)`

        # Arguments
            x: One or a list of containers to update.
            blkio_weight: Block IO (relative weight), between 10 and 1000,
                or 0 to disable (default 0)
            cpu_period: Limit CPU CFS (Completely Fair Scheduler) period
            cpu_quota: Limit CPU CFS (Completely Fair Scheduler) quota
            cpu_rt_period: Limit CPU real-time period in microseconds
            cpu_rt_runtime: Limit CPU real-time runtime in microseconds
            cpu_shares: CPU shares (relative weight)
            cpus: The maximal amount of cpu the container can use.
                `1` means one cpu core.
            cpuset_cpus: CPUs in which to allow execution. Must be given as a list.
            cpuset_mems: MEMs in which to allow execution. Must be given as a list.
            memory:  Memory limit, valid values are `1024` (ints are bytes) or
                `"43m"` or `"6g"`.
            memory_reservation: Memory soft limit
            memory_swap: Swap limit equal to memory plus swap: '-1'
                to enable unlimited swap.
            pids_limit: Tune container pids limit (set `-1` for unlimited)
            restart: Restart policy to apply when a container exits (default "no")
        """
        full_cmd = self.docker_cmd + ["container", "update"]
        full_cmd.add_simple_arg("--blkio-weight", blkio_weight)
        full_cmd.add_simple_arg("--cpu-period", cpu_period)
        full_cmd.add_simple_arg("--cpu-quota", cpu_quota)
        full_cmd.add_simple_arg("--cpu-rt-period", cpu_rt_period)
        full_cmd.add_simple_arg("--cpu-rt-runtime", cpu_rt_runtime)
        full_cmd.add_simple_arg("--cpu-shares", cpu_shares)
        full_cmd.add_simple_arg("--cpus", cpus)
        full_cmd.add_simple_arg("--cpuset-cpus", cpuset_cpus)
        full_cmd.add_simple_arg("--cpuset-mems", cpuset_mems)
        full_cmd.add_simple_arg("--kernel-memory", kernel_memory)
        full_cmd.add_simple_arg("--memory", memory)
        full_cmd.add_simple_arg("--memory-reservation", memory_reservation)
        full_cmd.add_simple_arg("--memory-swap", memory_swap)
        full_cmd.add_simple_arg("--pids-limit", pids_limit)
        full_cmd.add_simple_arg("--restart", restart)
        full_cmd += to_list(x)
        run(full_cmd)

    @overload
    def wait(self, x: ValidContainer) -> int:
        ...

    @overload
    def wait(self, x: List[ValidContainer]) -> List[int]:
        ...

    def wait(
        self, x: Union[ValidContainer, List[ValidContainer]]
    ) -> Union[int, List[int]]:
        """Block until one or more containers stop, then returns their exit codes

        Alias: `docker.wait(...)`


        # Arguments
            x: One or a list of containers to wait for.

        # Returns
            An `int` if a single container was passed as argument or a list of ints
            if multiple containers were passed as arguments.

        Some Examples:

        ```python
        cont = docker.run("ubuntu", ["bash", "-c", "sleep 2 && exit 8"], detach=True)

        exit_code = docker.wait(cont)

        print(exit_code)
        # 8
        docker.container.remove(cont)
        ```

        ```python
        cont_1 = docker.run("ubuntu", ["bash", "-c", "sleep 4 && exit 8"], detach=True)
        cont_2 = docker.run("ubuntu", ["bash", "-c", "sleep 2 && exit 10"], detach=True)

        exit_codes = docker.wait([cont_1, cont_2])

        print(exit_codes)
        # [8, 10]
        docker.container.remove([cont_1, cont_2])
        ```
        """
        full_cmd = self.docker_cmd + ["container", "wait"]
        if isinstance(x, list):
            full_cmd += x
            exit_codes = run(full_cmd)
            return [int(exit_code) for exit_code in exit_codes.splitlines()]
        else:
            full_cmd.append(x)
            return int(run(full_cmd))


class ContainerStats:
    def __init__(self, json_dict: Dict[str, Any]):
        """Takes a json_dict with container stats from the CLI and
        parses it.
        """
        self.block_read: int = pydantic.parse_obj_as(
            pydantic.ByteSize, json_dict["BlockIO"].split("/")[0]
        )
        self.block_write: int = pydantic.parse_obj_as(
            pydantic.ByteSize, json_dict["BlockIO"].split("/")[1]
        )
        self.cpu_percentage: float = float(json_dict["CPUPerc"][:-1])
        self.container: str = json_dict["Container"]
        self.container_id: str = json_dict["ID"]
        self.memory_percentage: float = float(json_dict["MemPerc"][:-1])
        self.memory_used: int = pydantic.parse_obj_as(
            pydantic.ByteSize, json_dict["MemUsage"].split("/")[0]
        )
        self.memory_limit: int = pydantic.parse_obj_as(
            pydantic.ByteSize, json_dict["MemUsage"].split("/")[1]
        )
        self.container_name: str = json_dict["Name"]
        self.net_upload: int = pydantic.parse_obj_as(
            pydantic.ByteSize, json_dict["NetIO"].split("/")[0]
        )
        self.net_download: int = pydantic.parse_obj_as(
            pydantic.ByteSize, json_dict["NetIO"].split("/")[1]
        )

    def __repr__(self):
        attr = ", ".join(f"{key}={value}" for key, value in self.__dict__.items())
        return f"<{self.__class__} object, attributes are {attr}>"


def format_time_for_docker(time_object: Union[datetime, timedelta]) -> str:
    if isinstance(time_object, datetime):
        return time_object.strftime("%Y-%m-%dT%H:%M:%S")
    elif isinstance(time_object, timedelta):
        return f"{time_object.total_seconds()}s"


def format_time_arg(time_object):
    if time_object is None:
        return None
    else:
        return format_time_for_docker(time_object)


def join_if_not_none(sequence: Optional[list]) -> Optional[str]:
    if sequence is None:
        return None
    sequence = [str(x) for x in sequence]
    return ",".join(sequence)


def to_seconds(duration: Union[None, int, timedelta]) -> Optional[str]:
    if duration is None:
        return None
    if isinstance(duration, timedelta):
        duration = int(duration.total_seconds())
    return f"{duration}s"
