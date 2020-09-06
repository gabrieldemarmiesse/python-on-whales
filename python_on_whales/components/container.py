import inspect
import json
from datetime import datetime, timedelta
from typing import Any, Dict, Iterator, List, Optional, Tuple, Union

from python_on_whales.client_config import (
    ClientConfig,
    DockerCLICaller,
    ReloadableObjectFromJson,
)
from python_on_whales.utils import (
    DockerCamelModel,
    ValidPath,
    removeprefix,
    run,
    to_list,
)

from .image import Image
from .volume import VolumeDefinition


class ContainerState(DockerCamelModel):
    status: str
    running: bool
    paused: bool
    restarting: bool
    OOM_killed: bool
    dead: bool
    pid: int
    exit_code: int
    error: str
    started_at: datetime
    finished_at: datetime


class ContainerInspectResult(DockerCamelModel):
    id: str
    created: datetime
    image: str
    name: str
    state: ContainerState


class Container(ReloadableObjectFromJson):
    def __init__(
        self, client_config: ClientConfig, reference: str, is_immutable_id=False
    ):
        super().__init__(client_config, "id", reference, is_immutable_id)

    def _fetch_inspect_result_json(self, reference):
        return run(self.docker_cmd + ["container", "inspect", reference])

    def _parse_json_object(self, json_object: Dict[str, Any]):
        return ContainerInspectResult.parse_obj(json_object)

    @property
    def id(self):
        return self._get_immutable_id()

    @property
    def name(self):
        return removeprefix(self._get_inspect_result().name, "/")

    @property
    def state(self) -> ContainerState:
        return self._get_inspect_result().state

    @property
    def image(self) -> Image:
        return Image(
            self.client_config, self._get_inspect_result().image, is_immutable_id=True
        )


ContainerPath = Tuple[Union[Container, str], ValidPath]
ValidContainer = Union[Container, str]


class ContainerCLI(DockerCLICaller):
    def list(self, all: bool = False) -> List[Container]:
        full_cmd = self.docker_cmd
        full_cmd += ["container", "list", "-q", "--no-trunc"]
        if all:
            full_cmd.append("--all")

        return [Container(self.client_config, x) for x in run(full_cmd).splitlines()]

    def remove(
        self,
        containers: Union[Container, str, List[Union[Container, str]]],
        force: bool = False,
        volumes=False,
    ) -> List[str]:
        full_cmd = self.docker_cmd + ["container", "rm"]

        if force:
            full_cmd.append("--force")
        if volumes:
            full_cmd.append("--volumes")

        for container in to_list(containers):
            full_cmd.append(str(container))

        return run(full_cmd).splitlines()

    def run(
        self,
        image: str,
        command: Optional[List[str]] = None,
        *,
        # add_host: Any = None,
        # attach: Any = None,
        blkio_weight: Optional[int] = None,
        # blkio_weight_device: Any = None,
        # cap_add: Any = None,
        # cap_drop: Any = None,
        # cgroup_parent: Any = None,
        # cidfile: Any = None,
        cpu_period: Optional[int] = None,
        cpu_quota: Optional[int] = None,
        cpu_rt_period: Optional[int] = None,
        cpu_rt_runtime: Optional[int] = None,
        cpu_shares: Optional[int] = None,
        cpus: Optional[float] = None,
        # cpuset_cpus: Any = None,
        # cpuset_mems: Any = None,
        detach: bool = False,
        # detach_keys: Any = None,
        # device: Any = None,
        # device_cgroup_rule: Any = None,
        # device_read_bps: Any = None,
        # device_read_iops: Any = None,
        # device_write_bps: Any = None,
        # device_write_iops: Any = None,
        # disable_content_trust: Any = None,
        # dns: Any = None,
        # dns_option: Any = None,
        # dns_search: Any = None,
        # domainname: Any = None,
        # entrypoint: Any = None,
        envs: Dict[str, str] = {},
        env_files: Union[ValidPath, List[ValidPath]] = [],
        # expose: Any = None,
        gpus: Optional[str] = None,
        # group_add: Any = None,
        # health_cmd: Any = None,
        # health_interval: Any = None,
        # health_retries: Any = None,
        # health_start_period: Any = None,
        # health_timeout: Any = None,
        hostname: Optional[str] = None,
        # init: Any = None,
        # interactive: Any = None,
        ip: Optional[str] = None,
        ip6: Optional[str] = None,
        ipc: Optional[str] = None,
        isolation: Optional[str] = None,
        kernel_memory: Union[int, str, None] = None,
        # label: Any = None,
        # label_file: Any = None,
        # link: Any = None,
        # link_local_ip: Any = None,
        log_driver: Optional[str] = None,
        # log_opt: Any = None,
        mac_address: Optional[str] = None,
        memory: Union[int, str, None] = None,
        memory_reservation: Union[int, str, None] = None,
        memory_swap: Union[int, str, None] = None,
        # memory_swappiness: Any = None,
        # mount: Any = None,
        name: Optional[str] = None,
        # network: Any = None,
        # network_alias: Any = None,
        healthcheck: bool = True,
        oom_kill: bool = True,
        # oom_score_adj: Any = None,
        pid: Optional[str] = None,
        pids_limit: Optional[int] = None,
        platform: Optional[str] = None,
        privileged: bool = False,
        # publish: Any = None,
        publish_all: bool = False,
        read_only: bool = False,
        restart: Optional[str] = None,
        rm: bool = False,
        runtime: Optional[str] = None,
        # security_opt: Any = None,
        shm_size: Union[int, str, None] = None,
        # sig_proxy: Any = None,
        # stop_signal: Any = None,
        stop_timeout: Optional[int] = None,
        # storage_opt: Any = None,
        # sysctl: Any = None,
        # tmpfs: Any = None,
        # tty: Any = None,
        # ulimit: Any = None,
        user: Optional[str] = None,
        userns: Optional[str] = None,
        uts: Optional[str] = None,
        volumes: Optional[List[VolumeDefinition]] = [],
        volume_driver: Optional[str] = None,
        # volumes_from: Any = None,
        workdir: Optional[ValidPath] = None,
    ) -> Union[Container, str]:
        full_cmd = self.docker_cmd + ["container", "run"]

        full_cmd.add_simple_arg("--blkio-weight", blkio_weight)
        full_cmd.add_simple_arg("--cpu-period", cpu_period)
        full_cmd.add_simple_arg("--cpu-quota", cpu_quota)
        full_cmd.add_simple_arg("--cpu-rt-period", cpu_rt_period)
        full_cmd.add_simple_arg("--cpu-rt-runtime", cpu_rt_runtime)
        full_cmd.add_simple_arg("--cpu-shares", cpu_shares)
        full_cmd.add_flag("--rm", rm)
        full_cmd.add_flag("--detach", detach)
        full_cmd.add_simple_arg("--name", name)
        full_cmd.add_simple_arg("--pid", pid)
        full_cmd.add_flag("--publish-all", publish_all)
        full_cmd.add_simple_arg("--isolation", isolation)
        full_cmd.add_simple_arg("--ipc", ipc)

        for env_file in to_list(env_files):
            full_cmd += ["--env-file", env_file]

        full_cmd.add_flag("--no-healthcheck", not healthcheck)
        full_cmd.add_flag("--oom-kill-disable", not oom_kill)

        for env_name, env_value in envs.items():
            full_cmd += ["--env", env_name + "=" + env_value]
        full_cmd.add_simple_arg("--mac-address", mac_address)
        full_cmd.add_simple_arg("--cpus", cpus)
        full_cmd.add_simple_arg("--log-driver", log_driver)
        full_cmd.add_simple_arg("--runtime", runtime)
        full_cmd.add_simple_arg("--hostname", hostname)
        full_cmd.add_simple_arg("--ip", ip)
        full_cmd.add_simple_arg("--ip6", ip6)
        full_cmd.add_simple_arg("--restart", restart)
        full_cmd.add_simple_arg("--pids-limit", pids_limit)
        full_cmd.add_flag("--privileged", privileged)
        full_cmd.add_simple_arg("--platform", platform)
        full_cmd.add_simple_arg("--kernel-memory", kernel_memory)

        for volume_definition in volumes:
            volume_definition = tuple(str(x) for x in volume_definition)
            full_cmd += ["--volume", ":".join(volume_definition)]

        full_cmd.add_simple_arg("--shm-size", shm_size)
        full_cmd.add_simple_arg("--memory", memory)
        full_cmd.add_simple_arg("--memory-reservation", memory_reservation)
        full_cmd.add_simple_arg("--memory-swap", memory_swap)
        full_cmd.add_simple_arg("--stop-timeout", stop_timeout)
        full_cmd.add_simple_arg("--gpus", gpus)
        full_cmd.add_flag("--read-only", read_only)
        full_cmd.add_simple_arg("--user", user)
        full_cmd.add_simple_arg("--userns", userns)
        full_cmd.add_simple_arg("--uts", uts)
        full_cmd.add_simple_arg("--volume-driver", volume_driver)
        full_cmd.add_simple_arg("--workdir", workdir)

        full_cmd.append(image)
        if command is not None:
            full_cmd += command

        if detach:
            return Container(self.client_config, run(full_cmd))
        else:
            return run(full_cmd)

    def logs(self, container: Union[Container, str]) -> str:
        full_cmd = self.docker_cmd + ["container", "logs"]

        return run(full_cmd + [str(container)])

    def cp(
        self,
        source: Union[bytes, Iterator[bytes], ValidPath, ContainerPath],
        destination: Union[None, ValidPath, ContainerPath],
    ):
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

    def kill(
        self,
        containers: Union[ValidContainer, List[ValidContainer]],
        signal: str = None,
    ):
        full_cmd = self.docker_cmd + ["container", "kill"]

        if signal is not None:
            full_cmd += ["--signal", signal]

        for container in to_list(containers):
            full_cmd.append(str(container))

        run(full_cmd)

    def stop(
        self,
        containers: Union[ValidContainer, List[ValidContainer]],
        time: Union[int, timedelta] = None,
    ):
        full_cmd = self.docker_cmd + ["container", "stop"]
        if isinstance(time, timedelta):
            time = time.total_seconds()

        if time is not None:
            full_cmd += ["--time", str(time)]

        for container in to_list(containers):
            full_cmd.append(str(container))

        run(full_cmd)

    def commit(
        self,
        container: ValidContainer,
        tag: Optional[str] = None,
        author: Optional[str] = None,
        message: Optional[str] = None,
        pause: bool = True,
    ):
        full_cmd = self.docker_cmd + ["container", "commit"]

        if author is not None:
            full_cmd += ["--author", author]

        if message is not None:
            full_cmd += ["--message", message]

        full_cmd += ["--pause", str(pause).lower()]

        full_cmd.append(str(container))
        if tag is not None:
            full_cmd.append(tag)

        return Image(self.client_config, run(full_cmd), is_immutable_id=True)

    def rename(self, container: ValidContainer, new_name: str) -> None:
        full_cmd = self.docker_cmd + ["container", "rename", str(container), new_name]
        run(full_cmd)

    def restart(
        self,
        containers: Union[ValidContainer, List[ValidContainer]],
        time: Optional[Union[int, timedelta]] = None,
    ):
        full_cmd = self.docker_cmd + ["restart"]

        if time is not None:
            if isinstance(time, timedelta):
                time = time.total_seconds()
            full_cmd += ["--time", str(time)]

        for container in to_list(containers):
            full_cmd.append(str(container))

        run(full_cmd)

    def pause(self, containers: Union[ValidContainer, List[ValidContainer]]):
        full_cmd = self.docker_cmd + ["pause"]
        for container in to_list(containers):
            full_cmd.append(str(container))

        run(full_cmd)

    def port(self, container: ValidContainer, private_port: Union[str, int] = None):
        raise NotImplementedError
