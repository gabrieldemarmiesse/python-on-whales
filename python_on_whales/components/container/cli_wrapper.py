from __future__ import annotations

import inspect
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union, overload

import pydantic

import python_on_whales.components.image.cli_wrapper
import python_on_whales.components.network.cli_wrapper
import python_on_whales.components.volume.cli_wrapper
from python_on_whales.client_config import (
    ClientConfig,
    DockerCLICaller,
    ReloadableObjectFromJson,
)
from python_on_whales.components.container.models import (
    ContainerConfig,
    ContainerGraphDriver,
    ContainerHostConfig,
    ContainerInspectResult,
    ContainerState,
    Mount,
    NetworkSettings,
)
from python_on_whales.exceptions import NoSuchContainer
from python_on_whales.utils import (
    ValidPath,
    format_dict_for_cli,
    format_time_arg,
    removeprefix,
    run,
    stream_stdout_and_stderr,
    to_list,
)


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
    ) -> python_on_whales.components.image.cli_wrapper.Image:
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

    def execute(
        self,
        command: Union[str, List[str]],
        detach: bool = False,
        envs: Dict[str, str] = {},
        env_files: Union[ValidPath, List[ValidPath]] = [],
        interactive: bool = False,
        privileged: bool = False,
        tty: bool = False,
        user: Optional[str] = None,
        workdir: Optional[ValidPath] = None,
        stream: bool = False,
    ) -> Union[None, str, Iterable[Tuple[str, bytes]]]:
        """Execute a command in this container

        See the [`docker.container.execute`](../sub-commands/container.md#execute)
        command for information about the arguments.
        """
        return ContainerCLI(self.client_config).execute(
            self,
            command,
            detach,
            envs,
            env_files,
            interactive,
            privileged,
            tty,
            user,
            workdir,
            stream,
        )

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

    def exists(self) -> bool:
        """Returns `True` if the docker container exists and `False` if it doesn't exists.

        If it doesn't exists, it most likely mean that it was removed.

         See the `docker.container.exists` command for information about the arguments.
        """
        return ContainerCLI(self.client_config).exists(self.id)


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
    ) -> python_on_whales.components.image.cli_wrapper.Image:
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

        return python_on_whales.components.image.cli_wrapper.Image(
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
        networks: List[
            python_on_whales.components.network.cli_wrapper.ValidNetwork
        ] = [],
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
            List[python_on_whales.components.volume.cli_wrapper.VolumeDefinition]
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
        python_on_whales.components.image.cli_wrapper.ImageCLI(
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
        full_cmd.add_args_list("--network-alias", network_aliases)

        full_cmd.add_flag("--oom-kill-disable", not oom_kill)
        full_cmd.add_simple_arg("--oom-score-adj", oom_score_adj)

        full_cmd.add_simple_arg("--pid", pid)
        full_cmd.add_simple_arg("--pids-limit", pids_limit)

        full_cmd.add_simple_arg("--platform", platform)
        full_cmd.add_flag("--privileged", privileged)

        self._add_publish_to_command(full_cmd, publish)
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

    def _add_publish_to_command(self, full_cmd, publish):
        for port_mapping in publish:
            if len(port_mapping) == 1:
                full_cmd += ["-p", port_mapping[0]]
            elif len(port_mapping) == 2:
                full_cmd += ["-p", f"{port_mapping[0]}:{port_mapping[1]}"]
            elif len(port_mapping) == 3:
                full_cmd += [
                    "-p",
                    f"{port_mapping[0]}:{port_mapping[1]}/{port_mapping[2]}",
                ]
            else:
                raise ValueError(
                    "The size of the tuples in the publish list must be 1, 2, or 3"
                )

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
        envs: Dict[str, str] = {},
        env_files: Union[ValidPath, List[ValidPath]] = [],
        interactive: bool = False,
        privileged: bool = False,
        tty: bool = False,
        user: Optional[str] = None,
        workdir: Optional[ValidPath] = None,
        stream: bool = False,
    ) -> Union[None, str, Iterable[Tuple[str, bytes]]]:
        """Execute a command inside a container

        Alias: `docker.execute(...)`

        # Arguments
            container: The container to execute the command in.
            command: The command to execute.
            detach: if `True`, returns immediately with `None`. If `False`,
                returns the command stdout as string.
            envs: Set environment variables
            env_files: Read one or more files of environment variables
            interactive: Leave stdin open during the duration of the process
                to allow communication with the parent process.
                Currently only works with `tty=True` for interactive use
                on the terminal.
            privileged: Give extended privileges to the container.
            tty: Allocate a pseudo-TTY. Allow the process to access your terminal
                to write on it.
            user: Username or UID, format: `"<name|uid>[:<group|gid>]"`
            workdir: Working directory inside the container
            stream: Similar to `docker.run(..., stream=True)`.

        # Returns:
            Optional[str]

        # Raises
            `python_on_whales.exceptions.NoSuchContainer` if the container does not exists.
        """
        full_cmd = self.docker_cmd + ["exec"]

        full_cmd.add_flag("--detach", detach)

        full_cmd.add_args_list("--env", format_dict_for_cli(envs))
        full_cmd.add_args_list("--env-file", env_files)

        # TODO: activate interactive and tty
        if interactive and not tty:
            raise NotImplementedError(
                "Currently, docker.container.execute(interactive=True) must have"
                "tty=True. interactive=True and tty=False is not yet implemented."
            )

        if interactive and stream:
            raise ValueError(
                "You can't set interactive=True and stream=True at the same"
                "time. Their purpose are not compatible."
            )

        if tty and stream:
            raise ValueError(
                "You can't set tty=True and stream=True at the same"
                "time. Their purpose are not compatible."
            )

        if detach and stream:
            raise ValueError(
                "You can't detach and stream at the same time. It's not compatible."
            )

        full_cmd.add_flag("--interactive", interactive)
        full_cmd.add_flag("--privileged", privileged)
        full_cmd.add_flag("--tty", tty)

        full_cmd.add_simple_arg("--user", user)
        full_cmd.add_simple_arg("--workdir", workdir)

        full_cmd.append(container)
        for arg in to_list(command):
            full_cmd.append(arg)
        if stream:
            return stream_stdout_and_stderr(full_cmd)
        else:
            result = run(full_cmd, tty=tty)
            if detach:
                return None
            else:
                return result

    def export(self, container: ValidContainer, output: ValidPath) -> None:
        """Export a container's filesystem as a tar archive

        Alias: `docker.export(...)`

        # Arguments
            container: The container to export.
            output: The path of the output tar archive. Returning a generator of bytes
                is not yet implemented.

        # Raises
            `python_on_whales.exceptions.NoSuchContainer` if the container does not exists.
        """
        full_cmd = self.docker_cmd + ["container", "export"]
        full_cmd.add_simple_arg("--output", output)

        full_cmd.append(container)

        if output is None:
            # we must return a generator of bytes
            raise NotImplementedError
        else:
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

        # Raises
            `python_on_whales.exceptions.NoSuchContainer` if the container does not exists.
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

        # Raises
            `python_on_whales.exceptions.NoSuchContainer` if the container does not exists.

        """
        containers = to_list(containers)
        if not containers:
            # nothing to do
            return
        full_cmd = self.docker_cmd + ["container", "kill"]

        full_cmd.add_simple_arg("--signal", signal)
        full_cmd += containers

        run(full_cmd)

    def logs(
        self,
        container: Union[Container, str],
        details: bool = False,
        since: Union[None, datetime, timedelta] = None,
        tail: Optional[int] = None,
        timestamps: bool = False,
        until: Union[None, datetime, timedelta] = None,
        follow: bool = False,
        stream: bool = False,
    ) -> Union[str, Iterable[Tuple[str, bytes]]]:
        """Returns the logs of a container as a string or an iterator.

        Alias: `docker.logs(...)`

        # Arguments
            container: The container to get the logs of
            details: Show extra details provided to logs
            since: Use a datetime or timedelta to specify the lower
                date limit for the logs.
            tail: Number of lines to show from the end of the logs (default all)
            timestamps: Put timestamps next to lines.
            until: Use a datetime or a timedelta to specify the upper date
                limit for the logs.
            follow: If `False` (the default), the logs returned are the logs up to the time
                of the function call. If `True`, the logs of the container up to the time the
                container stopped are displayed. Which means that if the container isn't stopped
                yet, the function will continue until the container is stopped.
                Which is why it is advised to use the `stream` option if you use the `follow` option.
                Without `stream`, only a `str` will be returned, possibly much later in the
                future. With `stream`, you'll be able to read the logs in real time.
            stream: Similar to the `stream` argument of `docker.run`.
                This function will then returns and iterator that will yield a
                tuple `(source, content)` with `source` being `"stderr"` or
                `"stdout"`. `content` is the content of the line as bytes.
                Take a look at [the user guide](https://gabrieldemarmiesse.github.io/python-on-whales/user_guide/docker_run/#stream-the-output)
                to have an example of the output.

        # Returns
            `str` if `stream=False` (the default), `Iterable[Tuple[str, bytes]]`
            if `stream=True`.

        # Raises
            `python_on_whales.exceptions.NoSuchContainer` if the container does not exists.

        If you are a bit confused about `follow` and `stream`, here are some use cases.

        * If you want to have the logs up to this point as a `str`, don't use those args.
        * If you want to stream the output in real time, use `follow=True, stream=True`
        * If you want the logs up to this point but you don't want to fit all the logs
        in memory because they are too big, use `stream=True`.
        """

        # first we verify that the container exists and raise an exception if not.
        self.inspect(container)

        full_cmd = self.docker_cmd + ["container", "logs"]
        full_cmd.add_flag("--details", details)
        full_cmd.add_simple_arg("--since", format_time_arg(since))
        full_cmd.add_simple_arg("--tail", tail)
        full_cmd.add_flag("--timestamps", timestamps)
        full_cmd.add_simple_arg("--until", format_time_arg(until))
        full_cmd.add_flag("--follow", follow)
        full_cmd.append(container)

        iterator = stream_stdout_and_stderr(full_cmd)

        if stream:
            return iterator
        else:
            return "".join(x[1].decode() for x in iterator)

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

        # Raises
            `python_on_whales.exceptions.NoSuchContainer` if the container does not exists.
        """
        containers = to_list(containers)
        if not containers:
            # nothing to do
            return
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

        # Raises
            `python_on_whales.exceptions.NoSuchContainer` if the container does not exists.
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

        # Raises
            `python_on_whales.exceptions.NoSuchContainer` if the container does not exists.
        """
        containers = to_list(containers)
        if not containers:
            # nothing to do
            return
        full_cmd = self.docker_cmd + ["restart"]

        if time is not None:
            if isinstance(time, timedelta):
                time = time.total_seconds()
            full_cmd += ["--time", str(time)]

        for container in containers:
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

        # Raises
            `python_on_whales.exceptions.NoSuchContainer` if the container does not exists.
        """
        containers = to_list(containers)
        if not containers:
            # nothing to do
            return
        full_cmd = self.docker_cmd + ["container", "rm"]
        full_cmd.add_flag("--force", force)
        full_cmd.add_flag("--volumes", volumes)

        for container in containers:
            full_cmd.append(str(container))

        run(full_cmd)

    def run(
        self,
        image: python_on_whales.components.image.cli_wrapper.ValidImage,
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
        interactive: bool = False,
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
        networks: List[
            python_on_whales.components.network.cli_wrapper.ValidNetwork
        ] = [],
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
        tty: bool = False,
        ulimit: List[str] = [],
        user: Optional[str] = None,
        userns: Optional[str] = None,
        uts: Optional[str] = None,
        volumes: Optional[
            List[python_on_whales.components.volume.cli_wrapper.VolumeDefinition]
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
            interactive: Leave stdin open during the duration of the process
                to allow communication with the parent process.
                Currently only works with `tty=True` for interactive use
                on the terminal.
            ip: IPv4 address (e.g., 172.30.100.104)
            ip6: IPv6 address (e.g., 2001:db8::33)
            ipc: IPC mode to use
            isolation: Container isolation technology
            kernel_memory: Kernel memory limit. `int` represents the number of bytes,
                but you can use `"4k"` or `2g` for example.
            labels: Set meta data on a container. The labels can be used later when filtering
                containers with `docker.ps(filters='...')`. The labels can also be found on
                each container with the attribute `my_container.config.labels`.
            log_driver: Logging driver for the container
            mac_address: Container MAC address (e.g., `"92:d0:c6:0a:29:33"`)
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
                `[("127.0.0.1:3000", 2000, "udp")]`. You can also use a single entry in
                the tuple to signify that you want a random free port on the host. For example:
                `publish=[(80,)]`.
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
            tty: Allocate a pseudo-TTY. Allow the process to access your terminal
                to write on it.
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

        python_on_whales.components.image.cli_wrapper.ImageCLI(
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

        # TODO: activate interactive and tty
        if interactive and not tty:
            raise NotImplementedError(
                "Currently, docker.container.run(interactive=True) must have"
                "tty=True. interactive=True and tty=False is not yet implemented."
            )
        full_cmd.add_flag("--interactive", interactive)
        full_cmd.add_flag("--tty", tty)

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
        full_cmd.add_args_list("--network-alias", network_aliases)

        full_cmd.add_flag("--oom-kill-disable", not oom_kill)
        full_cmd.add_simple_arg("--oom-score-adj", oom_score_adj)

        full_cmd.add_simple_arg("--pid", pid)
        full_cmd.add_simple_arg("--pids-limit", pids_limit)

        full_cmd.add_simple_arg("--platform", platform)
        full_cmd.add_flag("--privileged", privileged)

        self._add_publish_to_command(full_cmd, publish)
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

        if detach:
            if stream:
                raise ValueError(
                    "It's not possible to stream and detach a container at "
                    "the same time."
                )
            if interactive:
                raise ValueError(
                    "It's not possible to interact and detach a container at "
                    "the same time."
                )
        if stream and interactive:
            if interactive:
                raise ValueError(
                    "It's not possible to interact and stream a container at "
                    "the same time."
                )
        if detach:
            return Container(self.client_config, run(full_cmd))
        elif stream:
            return stream_stdout_and_stderr(full_cmd)
        else:
            return run(full_cmd, tty=tty, capture_stderr=False)

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
        containers = to_list(containers)
        if not containers:
            # nothing to do
            return
        if attach and len(containers) > 1:
            raise ValueError("Attaching multiple containers on start is not supported.")
        if not attach and stream:
            raise ValueError(
                "It's not possible to stream stderr and stdout if the client isn't "
                "attached to the container. Please set `attach=True`."
            )
        full_cmd = self.docker_cmd + ["container", "start"]
        full_cmd.add_flag("--attach", attach)
        full_cmd += containers

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

        # Raises
            `python_on_whales.exceptions.NoSuchContainer` if the container does not exists.
        """
        containers = to_list(containers)
        if not containers:
            # nothing to do
            return
        full_cmd = self.docker_cmd + ["container", "stop"]
        if isinstance(time, timedelta):
            time = time.total_seconds()

        if time is not None:
            full_cmd += ["--time", str(time)]

        for container in containers:
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

        # Raises
            `python_on_whales.exceptions.NoSuchContainer` if the container does not exists.
        """
        x = to_list(x)
        if not x:
            # nothing to do
            return
        full_cmd = self.docker_cmd + ["container", "unpause"]
        full_cmd += x
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

        # Raises
            `python_on_whales.exceptions.NoSuchContainer` if the container does not exists.
        """
        x = to_list(x)
        if not x:
            # nothing to do
            return
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
        full_cmd += x
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

        # Raises
            `python_on_whales.exceptions.NoSuchContainer` if the container does not exists.
        """
        if x == []:
            # nothing to do
            return []
        full_cmd = self.docker_cmd + ["container", "wait"]
        if isinstance(x, list):
            full_cmd += x
            exit_codes = run(full_cmd)
            return [int(exit_code) for exit_code in exit_codes.splitlines()]
        else:
            full_cmd.append(x)
            return int(run(full_cmd))

    def exists(self, x: str) -> bool:
        """Returns `True` if the container exists. `False` otherwise.

         It's just calling `docker.container.inspect(...)` and verifies that it doesn't throw
         a `python_on_whales.exceptions.NoSuchContainer`.

        # Returns
            A `bool`
        """
        try:
            self.inspect(x)
        except NoSuchContainer:
            return False
        else:
            return True


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
