import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import pydantic

import python_on_whales.components.node
from python_on_whales.client_config import DockerCLICaller
from python_on_whales.utils import DockerCamelModel, run


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
    volumes: List[str]
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
    node_id: str
    addr: str


class SwarmInfo(DockerCamelModel):
    node_id: str
    node_addr: str
    local_node_state: str
    control_available: bool
    error: str
    remote_managers: List[RemoteManager]


class SystemInfoResults(DockerCamelModel):
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
    cpu_shares: bool
    cpu_set: bool
    pids_limit: bool
    oom_kill_disable: bool
    ipv4_forwarding: bool
    bridge_nf_iptables: bool
    bridge_nf_ip6tables: bool
    debug: bool
    nfd: int = pydantic.Field(alias="NFd")
    n_goroutines: int
    system_time: str
    logging_driver: str
    cgroup_driver: str
    n_event_listener: int
    kernel_version: int
    operating_system: str
    os_type: str = pydantic.Field(alias="OSType")
    architecture: str
    n_cpu: int
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
    swarm: dict  # TODO
    live_restore_enabled: bool
    isolation: str
    init_binary: str
    containerd_commit: Commit
    runc_commit: Commit
    init_commit: Commit
    security_options: List[str]
    product_license: str
    warnings: List[str]


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

    def info(self):
        """Not yet implemented"""
        full_cmd = self.docker_cmd + ["system", "info", "--format", "{{json .}}"]
        return json.loads(run(full_cmd))

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
