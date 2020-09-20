import inspect
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

    def commit(
        self,
        tag: Optional[str] = None,
        author: Optional[str] = None,
        message: Optional[str] = None,
        pause: bool = True,
    ) -> Image:
        """Create a new image from the container's changes.

        See [The `docker.container.commit`](../sub-commands/container.md) command for
        information about the arguments.
        """
        return ContainerCLI(self.client_config).commit(
            self, tag, author, message, pause
        )

    def copy_from(self, container_path: ValidPath, local_path: ValidPath):
        return ContainerCLI(self.client_config).cp((self, container_path), local_path)

    def copy_to(self, local_path: ValidPath, container_path: ValidPath):
        return ContainerCLI(self.client_config).cp(local_path, (self, container_path))

    def diff(self) -> Dict[str, str]:
        return ContainerCLI(self.client_config).diff(self)

    def exec(self, command: Union[str, List[str]], detach: bool = False):
        return ContainerCLI(self.client_config).exec(self, command, detach)

    def export(self, output: ValidPath) -> None:
        return ContainerCLI(self.client_config).export(self, output)

    def kill(self, signal: str = None):
        return ContainerCLI(self.client_config).kill(self, signal)

    def logs(self) -> str:
        return ContainerCLI(self.client_config).logs(self)

    def pause(self) -> None:
        return ContainerCLI(self.client_config).pause(self)

    def rename(self, new_name: str) -> None:
        return ContainerCLI(self.client_config).rename(self, new_name)

    def restart(self, time: Optional[Union[int, timedelta]] = None) -> None:
        return ContainerCLI(self.client_config).restart(self, time)

    def remove(self, force: bool = False, volumes: bool = False) -> None:
        return ContainerCLI(self.client_config).remove(self, force, volumes)

    def start(self) -> None:
        return ContainerCLI(self.client_config).start(self)

    def stop(self, time: Union[int, timedelta] = None) -> None:
        return ContainerCLI(self.client_config).stop(self, time)


ContainerPath = Tuple[Union[Container, str], ValidPath]
ValidContainer = Union[Container, str]
ValidPortMapping = Union[
    Tuple[Union[str, int], Union[str, int]],
    Tuple[Union[str, int], Union[str, int], str],
]


class ContainerCLI(DockerCLICaller):
    def commit(
        self,
        container: ValidContainer,
        tag: Optional[str] = None,
        author: Optional[str] = None,
        message: Optional[str] = None,
        pause: bool = True,
    ) -> Image:
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

        full_cmd += ["--pause", str(pause).lower()]

        full_cmd.append(str(container))
        if tag is not None:
            full_cmd.append(tag)

        return Image(self.client_config, run(full_cmd), is_immutable_id=True)

    def cp(
        self,
        source: Union[ValidPath, ContainerPath],
        destination: Union[ValidPath, ContainerPath],
    ):
        """Copy files/folders between a container and the local filesystem

        ```python
        from python_on_whales import docker

        docker.run("ubuntu", ["sleep", "infinity"], name="dodo", rm=True)

        docker.cp("/tmp/my_local_file.txt", ("dodo", "/path/in/container.txt"))
        docker.cp(("dodo", "/path/in/container.txt"), "/tmp/my_local_file2.txt")
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
        volumes: Optional[List[VolumeDefinition]] = [],
    ) -> Container:
        """Creates a container.

        # Arguments
            image: The docker image to create the container from.
        """
        full_cmd = self.docker_cmd + ["create"]

        for volume_definition in volumes:
            volume_definition = tuple(str(x) for x in volume_definition)
            full_cmd += ["--volume", ":".join(volume_definition)]

        full_cmd.append(image)
        return Container(self.client_config, run(full_cmd), is_immutable_id=True)

    def diff(self, container: ValidContainer) -> Dict[str, str]:
        """List all the files modified, added or deleted since the container started.

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

    def exec(
        self,
        container: ValidContainer,
        command: Union[str, List[str]],
        detach: bool = False,
    ) -> Optional[str]:
        """Execute a command inside a container

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
        full_cmd = self.docker_cmd + [
            "container",
            "--output",
            output,
            "export",
            container,
        ]
        run(full_cmd)

    def inspect(self, reference: str) -> Container:
        """Returns a container object from a name or ID.

        # Arguments
            reference: A container name or ID.

        # Returns:
            A `python_on_whales.Container` object.

        """
        return Container(self.client_config, reference)

    def kill(
        self,
        containers: Union[ValidContainer, List[ValidContainer]],
        signal: str = None,
    ):
        """Kill a container.

        # Arguments
            containers: One or more containers to kill
            signal: The signal to send the container
        """
        full_cmd = self.docker_cmd + ["container", "kill"]

        if signal is not None:
            full_cmd += ["--signal", signal]

        for container in to_list(containers):
            full_cmd.append(str(container))

        run(full_cmd)

    def logs(self, container: Union[Container, str]) -> str:
        full_cmd = self.docker_cmd + ["container", "logs"]

        return run(full_cmd + [str(container)])

    def list(self, all: bool = False) -> List[Container]:
        """List the containers on the host.

        # Arguments
            all: If `True`, also returns containers that are not running.

        # Returns
            A `List[python_on_whales.Container]`
        """
        full_cmd = self.docker_cmd
        full_cmd += ["container", "list", "-q", "--no-trunc"]
        if all:
            full_cmd.append("--all")

        return [Container(self.client_config, x) for x in run(full_cmd).splitlines()]

    def pause(self, containers: Union[ValidContainer, List[ValidContainer]]):
        """Pauses one or more containers

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
        full_cmd = self.docker_cmd + ["container", "rm"]
        full_cmd.add_flag("--force", force)
        full_cmd.add_flag("--volumes", volumes)

        for container in to_list(containers):
            full_cmd.append(str(container))

        run(full_cmd).splitlines()

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
        gpus: Union[int, str, None] = None,
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
        publish: List[ValidPortMapping] = [],
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
        """Runs a container

        You can use `docker.run` or `docker.container.run` to call this function.

        For a deeper dive into the arguments and what they do, visit
        <https://docs.docker.com/engine/reference/run/>

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
            blkio_weight:Block IO (relative weight), between 10 and 1000,
                or 0 to disable (default 0)
            cpu_period: Limit CPU CFS (Completely Fair Scheduler) period
            cpu_quota: Limit CPU CFS (Completely Fair Scheduler) quota
            cpu_rt_period: Limit CPU real-time period in microseconds
            cpu_rt_runtime: Limit CPU real-time runtime in microseconds
            cpu_shares: CPU shares (relative weight)
            cpus: The maximal amount of cpu the container can use.
                `1` means one cpu core.
            detach: If `False`, returns the ouput of the container as a string.
                If `True`, returns a `python_on_whales.Container` object.
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
            publish: Ports to publish, same as the `-p` argument in the Docker CLI.
                example are `[(8000, 7000) , ("127.0.0.1:3000", 2000)]` or
                `[("127.0.0.1:3000", 2000, "udp")]`.
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

        for port_mapping in publish:
            if len(port_mapping) == 2:
                full_cmd += ["-p", f"{port_mapping[0]}:{port_mapping[1]}"]
            else:
                full_cmd += [
                    "-p",
                    f"{port_mapping[0]}:{port_mapping[1]}/{port_mapping[2]}",
                ]

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

    def start(self, containers: Union[ValidContainer, List[ValidContainer]]) -> None:
        """Starts one or more stopped containers.

        Aliases: `docker.start`, `docker.container.start`,
        `python_on_whales.Container.start`.

        # Arguments
            containers: One or a list of containers.
        """
        full_cmd = self.docker_cmd + ["container", "start"]
        for container in to_list(containers):
            full_cmd.append(container)
        run(full_cmd)

    def stop(
        self,
        containers: Union[ValidContainer, List[ValidContainer]],
        time: Union[int, timedelta] = None,
    ):
        """Stops one or more running containers

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
            full_cmd.append(str(container))

        run(full_cmd)
