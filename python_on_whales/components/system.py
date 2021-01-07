import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pydantic

import python_on_whales.components.node
from python_on_whales.client_config import DockerCLICaller
from python_on_whales.utils import DockerCamelModel, run


class DockerEventActor(DockerCamelModel):
    id: str = pydantic.Field(alias="ID")
    attributes: Dict[str, Any]


class DockerEvent(DockerCamelModel):
    type: str
    action: str
    actor: DockerEventActor
    time: datetime
    time_nano: int = pydantic.Field(alias="timeNano")


class DockerItemsSummary(DockerCamelModel):
    active: int
    reclaimable: pydantic.ByteSize
    reclaimable_percent: float
    size: pydantic.ByteSize
    total_count: int


class DiskFreeResult:
    def __init__(self, cli_stdout: str):
        docker_items = {}
        for line in cli_stdout.splitlines():
            docker_items_dict = json.loads(line)
            reclamable = docker_items_dict["Reclaimable"]
            docker_items_dict["Reclaimable"] = reclamable.split(" ")[0]
            if "%" in reclamable:
                docker_items_dict["ReclaimablePercent"] = reclamable.split(" ")[1][1:-2]
            else:
                docker_items_dict["ReclaimablePercent"] = "100"

            docker_items[docker_items_dict["Type"]] = docker_items_dict

        self.images: DockerItemsSummary
        self.images = DockerItemsSummary.parse_obj(docker_items["Images"])
        self.containers: DockerItemsSummary
        self.containers = DockerItemsSummary.parse_obj(docker_items["Containers"])
        self.volumes: DockerItemsSummary
        self.volumes = DockerItemsSummary.parse_obj(docker_items["Local Volumes"])
        self.build_cache: DockerItemsSummary
        self.build_cache = DockerItemsSummary.parse_obj(docker_items["Build Cache"])


class Plugins(DockerCamelModel):
    volume: List[str]
    network: List[str]
    authorization: Any
    log: List[str]


class Runtime(DockerCamelModel):
    path: str
    runtime_args: Optional[List[str]]


class Commit(DockerCamelModel):
    id: str = pydantic.Field(alias="ID")
    expected: str


class RemoteManager(DockerCamelModel):
    node_id: str = pydantic.Field(alias="NodeID")
    addr: str


class Orchestration(DockerCamelModel):
    task_history_retention_limit: int


class Raft(DockerCamelModel):
    snapshot_interval: int
    keep_old_snapshots: int
    log_entries_for_slow_followers: int
    election_tick: int
    heartbeat_tick: int


class SwarmDispatcher(DockerCamelModel):
    heartbeat_period: int


class SwarmCAConfig(DockerCamelModel):
    node_cert_expiry: int
    external_ca: Optional[List[Any]] = pydantic.Field(
        alias="ExternalCA"
    )  # TODO: set type
    signing_ca_cert: Optional[str] = pydantic.Field(alias="SigningCACert")
    signing_ca_key: Optional[str] = pydantic.Field(alias="SigningCAKey")
    force_rotate: Optional[int]


class SwarmEncryptionConfig(DockerCamelModel):
    auto_lock_managers: bool


class Driver(DockerCamelModel):
    name: str
    options: Dict[str, Any]


class SwarmTasksDefault(DockerCamelModel):
    log_driver: Optional[Driver]


class SwarmSpec(DockerCamelModel):
    name: str
    labels: Dict[str, str]
    orchestration: Optional[Orchestration]
    raft: Raft
    dispatcher: Optional[SwarmDispatcher]
    ca_config: Optional[SwarmCAConfig] = pydantic.Field(alias="CAConfig")
    encryption_config: SwarmEncryptionConfig
    task_defaults: SwarmTasksDefault


class ClusterInfo(DockerCamelModel):
    id: str = pydantic.Field(alias="ID")
    version: python_on_whales.components.node.NodeVersion
    created_at: datetime
    updated_at: datetime
    spec: SwarmSpec
    tls_info: python_on_whales.components.node.NodeTLSInfo
    root_rotation_in_progress: bool
    data_path_port: int
    default_addr_pool: List[str]
    subnet_size: int


class SwarmInfo(DockerCamelModel):
    node_id: str = pydantic.Field(alias="NodeID")
    node_addr: str
    local_node_state: str
    control_available: bool
    error: str
    remote_managers: Optional[List[RemoteManager]]
    nodes: Optional[int]
    managers: Optional[int]
    cluster: Optional[ClusterInfo]


class ClientPlugin(DockerCamelModel):
    schema_version: str
    vendor: str
    version: str
    short_description: str
    name: str
    path: Path
    shadowed_paths: Optional[List[Path]]


class ClientInfo(DockerCamelModel):
    debug: bool
    plugins: List[ClientPlugin]
    warnings: Optional[List[str]]


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
    system_status: Optional[List[str]]
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
    generic_resources: Optional[
        List[python_on_whales.components.node.NodeGenericResource]
    ]
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
    product_license: Optional[str]
    warnings: Optional[List[str]]
    client_info: ClientInfo


class SystemCLI(DockerCLICaller):
    def disk_free(self) -> DiskFreeResult:
        """Give information about the disk usage of the Docker daemon.

        Returns a `python_on_whales.DiskFreeResult` object.

        ```python
        from python_on_whales import docker
        disk_free_result = docker.system.disk_free()
        print(disk_free_result.images.active)  #int
        print(disk_free_result.containers.reclaimable)  # int, number of bytes
        print(disk_free_result.volumes.reclaimable_percent)  # float
        print(disk_free_result.build_cache.total_count)  # int
        print(disk_free_result.build_cache.size)  # int, number of bytes
        ...
        ```
        Note that the number are not 100% accurate because the docker CLI
        doesn't provide the exact numbers.

        Maybe in a future implementation, we can provide exact numbers.

        Verbose mode is not yet implemented.
        """

        full_cmd = self.docker_cmd + ["system", "df", "--format", "{{json .}}"]
        return DiskFreeResult(run(full_cmd))

    def events(self):
        """Not yet implemented"""
        raise NotImplementedError

    def info(self) -> SystemInfo:
        """Returns diverse information about the Docker client and daemon.

        # Returns
            A `python_on_whales.SystemInfo` object

        As an example

        ```python
        from python_on_whales import docker

        info = docker.system.info()
        print(info.images)
        # 40
        print(info.plugins.volume)
        # ["local"}
        ...
        ```

        You can find all attributes available by looking up the [reference page for
        system info](https://docs.docker.com/engine/api/v1.40/#operation/SystemInfo).
        """
        full_cmd = self.docker_cmd + ["system", "info", "--format", "{{json .}}"]
        return SystemInfo.parse_raw(run(full_cmd))

    def prune(self, all: bool = False, volumes: bool = False) -> None:
        """Remove unused docker data

        # Arguments
            all: Remove all unused images not just dangling ones
            volumes: Prune volumes
        """
        full_cmd = self.docker_cmd + ["system", "prune"]
        full_cmd.add_flag("--all", all)
        full_cmd.add_flag("--volumes", volumes)
        run(full_cmd)
