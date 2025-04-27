from __future__ import annotations

import json
import warnings
from datetime import datetime, timedelta
from typing import (
    Any,
    Iterable,
    List,
    Literal,
    Mapping,
    Optional,
    Tuple,
    Union,
    overload,
)

from typing_extensions import TypeAlias

import python_on_whales.components.container.cli_wrapper
import python_on_whales.components.image.cli_wrapper
import python_on_whales.components.network.cli_wrapper
from python_on_whales.client_config import (
    ClientConfig,
    DockerCLICaller,
    ReloadableObjectFromJson,
)
from python_on_whales.components.pod.models import (
    PodContainer,
    PodInfraConfig,
    PodInspectResult,
)
from python_on_whales.components.volume.cli_wrapper import VolumeDefinition
from python_on_whales.exceptions import NoSuchPod
from python_on_whales.utils import (
    ValidPath,
    ValidPortMapping,
    format_port_arg,
    format_signal_arg,
    format_time_arg,
    join_if_not_none,
    run,
    stream_stdout_and_stderr,
    to_list,
)

PodListFilter: TypeAlias = Union[
    Tuple[Literal["ctr-ids"], str],
    Tuple[Literal["ctr-names"], str],
    Tuple[Literal["ctr-number"], int],
    Tuple[Literal["ctr-status"], str],
    Tuple[Literal["id"], str],
    Tuple[Literal["label"], str],
    Tuple[Literal["label!"], str],
    Tuple[Literal["name"], str],
    Tuple[Literal["network"], str],  # TODO: allow Network
    Tuple[Literal["status"], str],
    Tuple[Literal["until"], str],  # TODO: allow datetime
]


class Pod(ReloadableObjectFromJson):
    def __init__(
        self, client_config: ClientConfig, reference: str, is_immutable_id=False
    ):
        super().__init__(client_config, "id", reference, is_immutable_id)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.remove(force=True)

    def _fetch_inspect_result_json(self, reference):
        json_str = run(self.docker_cmd + ["pod", "inspect", reference])
        return json.loads(json_str)

    def _parse_json_object(self, json_object: Mapping[str, Any]) -> PodInspectResult:
        return PodInspectResult(**json_object)

    def _get_inspect_result(self) -> PodInspectResult:
        """Only there to allow tools to know the return type"""
        return super()._get_inspect_result()

    @property
    def id(self) -> str:
        return self._get_immutable_id()

    @property
    def name(self) -> str:
        return self._get_inspect_result().name

    @property
    def created(self) -> datetime:
        return self._get_inspect_result().created

    @property
    def create_command(self) -> Optional[List[str]]:
        return self._get_inspect_result().create_command

    @property
    def exit_policy(self) -> Optional[str]:
        return self._get_inspect_result().exit_policy

    @property
    def state(self) -> Optional[str]:
        return self._get_inspect_result().state

    @property
    def hostname(self) -> Optional[str]:
        return self._get_inspect_result().hostname

    @property
    def labels(self) -> Mapping[str, str]:
        return self._get_inspect_result().labels

    @property
    def create_cgroup(self) -> Optional[bool]:
        return self._get_inspect_result().create_cgroup

    @property
    def cgroup_parent(self) -> Optional[str]:
        return self._get_inspect_result().cgroup_parent

    @property
    def cgroup_path(self) -> Optional[str]:
        return self._get_inspect_result().cgroup_path

    @property
    def create_infra(self) -> Optional[bool]:
        return self._get_inspect_result().create_infra

    @property
    def infra_container_id(self) -> Optional[str]:
        return self._get_inspect_result().infra_container_id

    @property
    def infra_config(self) -> Optional[PodInfraConfig]:
        return self._get_inspect_result().infra_config

    @property
    def shared_namespaces(self) -> Optional[List[str]]:
        return self._get_inspect_result().shared_namespaces

    @property
    def num_containers(self) -> Optional[int]:
        return self._get_inspect_result().num_containers

    @property
    def containers(self) -> Optional[List[PodContainer]]:
        return self._get_inspect_result().containers

    def __repr__(self):
        return f"python_on_whales.Pod(id='{self.id[:20]}', name={self.name})"

    def exists(self) -> bool:
        """Returns `True` if the pod exists and `False` if not.

        See the `podman.pod.exists` command for information about the arguments.
        """
        return PodCLI(self.client_config).exists(self.id)

    def kill(self, *, signal: Optional[Union[int, str]] = None) -> None:
        """Kill this pod

        See the [`podman.pod.kill`](../sub-commands/container.md#kill) command for
        information about the arguments.
        """
        return PodCLI(self.client_config).kill(self, signal=signal)

    def logs(
        self,
        container: Optional[
            python_on_whales.components.container.cli_wrapper.ValidContainer
        ] = None,
        *,
        names: bool = False,
        since: Union[None, datetime, timedelta] = None,
        tail: Optional[int] = None,
        timestamps: bool = False,
        until: Union[None, datetime, timedelta] = None,
        follow: bool = False,
        stream: bool = False,
    ) -> Union[str, Iterable[Tuple[str, bytes]]]:
        """Returns the logs of the pod containers

        See the [`podman.pod.logs`](../sub-commands/pod.md#logs) command for
        information about the arguments.
        """
        return PodCLI(self.client_config).logs(
            self,
            container=container,
            names=names,
            since=since,
            tail=tail,
            timestamps=timestamps,
            until=until,
            follow=follow,
            stream=stream,
        )

    def pause(self) -> None:
        """Pause this pod.

        See the [`podman.pod.pause`](../sub-commands/pod.md#pause) command for
        information about the arguments.
        """
        return PodCLI(self.client_config).pause(self)

    def unpause(self) -> None:
        """Unpause the pod

        See the [`podman.pod.unpause`](../sub-commands/pod.md#unpause) command for
        information about the arguments.
        """
        return PodCLI(self.client_config).unpause(self)

    def restart(self) -> None:
        """Restart this pod.

        See the [`podman.pod.restart`](../sub-commands/pod.md#restart) command for
        information about the arguments.
        """
        return PodCLI(self.client_config).restart(self)

    def remove(self, *, force: bool = False, time: Optional[int] = None) -> None:
        """Remove this pod.

        See the [`podman.pod.remove`](../sub-commands/pod.md#remove) command for
        information about the arguments.
        """
        PodCLI(self.client_config).remove(self, force=force, time=time)

    def start(self) -> Union[None, str, Iterable[Tuple[str, bytes]]]:
        """Starts this pod.

        See the [`podman.pod.start`](../sub-commands/pod.md#start) command for
        information about the arguments.
        """
        return PodCLI(self.client_config).start(self)

    def stop(self, *, time: Optional[int] = None) -> None:
        """Stops this pod.

        See the [`podman.pod.stop`](../sub-commands/pod.md#stop) command for
        information about the arguments.
        """
        return PodCLI(self.client_config).stop(self, time=time)


ValidPod = Union[str, Pod]


class PodCLI(DockerCLICaller):
    def create(
        self,
        name: Optional[str] = None,
        *,
        add_hosts: Iterable[Tuple[str, str]] = (),
        cgroup_parent: Optional[str] = None,
        cpus: Optional[float] = None,
        cpuset_cpus: Optional[Iterable[int]] = None,
        devices: Iterable[str] = (),
        device_read_bps: Iterable[str] = (),
        dns: Iterable[str] = (),
        dns_options: Iterable[str] = (),
        dns_search: Iterable[str] = (),
        exit_policy: Optional[str] = None,
        gidmaps: Iterable[Tuple[int, int, int]] = (),
        hostname: Optional[str] = None,
        infra: Optional[bool] = None,
        infra_command: Optional[str] = None,
        infra_conmon_pidfile: Optional[ValidPath] = None,
        infra_image: Optional[
            python_on_whales.components.image.cli_wrapper.ValidImage
        ] = None,
        infra_name: Optional[str] = None,
        ip: Optional[str] = None,
        ip6: Optional[str] = None,
        labels: Mapping[str, str] = {},
        label_files: Iterable[ValidPath] = (),
        mac_address: Optional[str] = None,
        memory: Union[int, str, None] = None,
        networks: Iterable[
            python_on_whales.components.network.cli_wrapper.ValidNetwork
        ] = (),
        network_aliases: Iterable[str] = (),
        no_hosts: bool = False,
        pid: Optional[str] = None,
        pod_id_file: Optional[ValidPath] = None,
        publish: Iterable[ValidPortMapping] = (),
        replace: bool = False,
        restart: Optional[str] = None,
        security_options: Iterable[str] = (),
        share: Optional[Iterable[str]] = None,
        shm_size: Optional[Union[int, str]] = None,
        subgidname: Optional[str] = None,
        subuidname: Optional[str] = None,
        sysctl: Mapping[str, str] = {},
        uidmaps: Iterable[Tuple[int, int, int]] = (),
        userns: Optional[str] = None,
        uts: Optional[str] = None,
        volumes: Iterable[VolumeDefinition] = (),
        volumes_from: Iterable[
            python_on_whales.components.container.cli_wrapper.ValidContainer
        ] = (),
    ) -> Pod:
        """Creates a pod, but does not start it.

        Start it then with the `.start()` method.

        Parameters:
            name: The name to set the pod to. If not specified a name is
                generated.
            add_hosts: Add a custom host-to-IP mapping (format 'host:ip'), which
                adds a line to /etc/hosts. Conflicts with the no_hosts option.
            cgroup_parent: Path to cgroups under which the cgroup for the pod is
                created. If the path is not absolute, the path is considered to
                be relative to the cgroups path of the init process.
            cpus: Set the total number of CPUs delegated to the pod. The default
                is 0.0 indicating that there is no limit on computation power.
            cpuset_cpus: CPUs in which to allow execution.
            devices: List of device names to pass from the host to containers
                in the pod.
            device_read_bps: Limit read rate (in bytes per second) from a device
                (e.g. device_read_bps=/dev/sda:1mb).
            dns: Set custom DNS servers in the /etc/resolv.conf file that is
                shared between all containers in the pod.
            dns_options: Set custom DNS options in the /etc/resolv.conf file
                that is shared between all containers in the pod.
            dns_search: Set custom DNS search domains in the /etc/resolv.conf
                file that is shared between all containers in the pod.
            exit_policy: Set the exit policy of the pod when the last container
                exits. Supported policies are 'continue' (default) and 'stop'.
            gidmaps: GID map for the user namespace. Using this flag runs all
                containers in the pod with user namespace enabled. It conflicts
                with the --userns and --subgidname flags.
            hostname: Set the pod's hostname.
            infra: Whether to create an infra container and associate it with
                the pod. An infra container is a lightweight container used to
                coordinate the shared kernel namespace of a pod.
            infra_command: Specify the command that is run to start the infra
                container.
            infra_conmon_pidfile: Write the pid of the infra container's conmon
                process to a file.
            infra_image: The custom image that is used for the infra container.
            infra_name: The name that is used for the pod's infra container.
            ip: Specify a static IPv4 address for the pod, for example
                10.88.64.128. This option can only be used if the pod is joined
                to only a single network - i.e., network=network-name is used at
                most once - and if the pod is not joining another container's
                network namespace via network=container:id. The address must be
                within the network's IP address pool (default 10.88.0.0/16).
            ip6: Specify a static IPv6 address for the pod, for example
                fd46:db93:aa76:ac37::10. This option can only be used if the pod is
                joined to only a single network (see note on the ip argument).
                The address must be within the network's IPv6 address pool.
            labels: Add metadata labels to a pod.
            label_files: Read in a line-delimited file of labels.
            mac_address: Pod network interface MAC address
                (e.g. 92:d0:c6:0a:29:33). This option can only be used if the
                pod is joined to only a single network (see note on the ip
                argument).
            memory: Memory limit for the pod.
            networks: Specify networks to use for the pod.
            network_aliases: Add network-scoped aliases for the pod, setting the
                alias for all networks that the container joins.
            no_hosts: Do not create /etc/hosts for the pod. This option
                conflicts with --add-host.
            pid: Set the PID mode for the pod. The default is to create a
                private PID namespace for the pod.
            pod_id_file: Write the pod ID to the specified file.
            publish: Publish a container's port, or range of ports, within this
                pod to the host.
            replace: If another pod with the same name already exists, replace
                and remove it.
            restart: Restart policy for containers in the pod.
            security_options: Security options (AppArmor or SELinux).
            share: Namespaces to share between containers in the pod.
            shm_size: Size of /dev/shm.
            subgidname: Run the container in a new user namespace using the map
                with name in the /etc/subgid file.
            subuidname: Run the container in a new user namespace using the map
                with name in the /etc/subuid file.
            sysctl: Configure namespaced kernel parameters for all containers in
                the pod.
            uidmaps: Run all containers in the pod in a new user namespace using
                the supplied UID mapping. This option conflicts with the userns
                and subuidname options.
            userns: Set the user namespace mode for all the containers in a pod.
            uts: Set the UTS namespace mode for the pod.
            volumes: Specify volumes passed to all containers in the pod.
            volumes_from: Mount volumes from the specified container(s).

        # Returns
            A `python_on_whales.Pod` object.
        """
        full_cmd = self.docker_cmd + ["pod", "create"]
        full_cmd.add_simple_arg("--name", name)

        full_cmd.add_args_iterable(
            "--add-host", [f"{host}:{ip}" for host, ip in add_hosts]
        )
        full_cmd.add_simple_arg("--cgroup-parent", cgroup_parent)
        full_cmd.add_simple_arg("--cpus", cpus)
        full_cmd.add_simple_arg("--cpuset-cpus", join_if_not_none(cpuset_cpus))
        full_cmd.add_args_iterable("--device", devices)
        full_cmd.add_args_iterable("--device-read-bps", device_read_bps)
        full_cmd.add_args_iterable("--dns", dns)
        full_cmd.add_args_iterable("--dns-option", dns_options)
        full_cmd.add_args_iterable("--dns-search", dns_search)
        full_cmd.add_simple_arg("--exit-policy", exit_policy)
        full_cmd.add_args_iterable("--gidmap", [":".join(x) for x in gidmaps])
        full_cmd.add_simple_arg("--hostname", hostname)

        if infra is not None:
            # Must be specified as single argument to override with False.
            full_cmd.append(f"--infra={infra!s}")
        full_cmd.add_simple_arg("--infra-command", infra_command)
        full_cmd.add_simple_arg("--infra-conmon-pidfile", infra_conmon_pidfile)
        full_cmd.add_simple_arg("--infra-image", infra_image)
        full_cmd.add_simple_arg("--infra-name", infra_name)

        full_cmd.add_simple_arg("--ip", ip)
        full_cmd.add_simple_arg("--ip6", ip6)
        full_cmd.add_args_mapping("--label", labels)
        full_cmd.add_args_iterable_or_single("--label-file", label_files)
        full_cmd.add_simple_arg("--mac-address", mac_address)
        full_cmd.add_simple_arg("--memory", memory)
        full_cmd.add_args_iterable_or_single("--network", networks)
        full_cmd.add_args_iterable("--network-alias", network_aliases)
        full_cmd.add_flag("--no-hosts", no_hosts)
        full_cmd.add_simple_arg("--pid", pid)
        full_cmd.add_simple_arg("--pod-id-file", pod_id_file)
        full_cmd.add_args_iterable("-p", [format_port_arg(p) for p in publish])
        full_cmd.add_flag("--replace", replace)
        full_cmd.add_simple_arg("--restart", restart)
        full_cmd.add_args_iterable("--security-opt", security_options)
        if share is not None:
            full_cmd.add_simple_arg("--share", ",".join(share))
        full_cmd.add_simple_arg("--shm-size", shm_size)
        full_cmd.add_simple_arg("--subgidname", subgidname)
        full_cmd.add_simple_arg("--subuidname", subuidname)
        full_cmd.add_args_mapping("--sysctl", sysctl)
        full_cmd.add_args_iterable_or_single("--uidmap", [":".join(x) for x in uidmaps])
        full_cmd.add_simple_arg("--userns", userns)
        full_cmd.add_simple_arg("--uts", uts)
        for volume_definition in volumes:
            full_cmd += ["--volume", ":".join(str(x) for x in volume_definition)]
        full_cmd.add_args_iterable_or_single("--volumes-from", volumes_from)

        return Pod(self.client_config, run(full_cmd), is_immutable_id=True)

    def exists(self, pod: ValidPod) -> bool:
        """Returns `True` if the pod exists. `False` otherwise.

         It's just calling `podman.pod.inspect(...)` and verifies that it doesn't throw
         a `python_on_whales.exceptions.NoSuchPod`.

        # Returns
            A `bool`
        """
        try:
            self.inspect(pod)
        except NoSuchPod:
            return False
        else:
            return True

    @overload
    def inspect(self, x: ValidPod, /) -> Pod: ...

    @overload
    def inspect(self, x: Iterable[ValidPod], /) -> List[Pod]: ...

    def inspect(
        self, x: Union[ValidPod, Iterable[ValidPod]], /
    ) -> Union[Pod, List[Pod]]:
        """Creates a `python_on_whales.Pod` object.

        # Returns
            `python_on_whales.Pod`, or `List[python_on_whales.Pod]` if the input
            was a list of strings.

        # Raises
            `python_on_whales.exceptions.NoSuchPod` if one of the pods does not exist.

        """
        if isinstance(x, list):
            return [Pod(self.client_config, identifier) for identifier in x]
        else:
            return Pod(self.client_config, x)

    def kill(
        self,
        x: Union[ValidPod, Iterable[ValidPod]],
        /,
        *,
        signal: Optional[Union[int, str]] = None,
    ) -> None:
        """Kill pods.

        Parameters:
            x: One or more pods to kill
            signal: The signal to send the pods' containers

        # Raises
            `python_on_whales.exceptions.NoSuchPod` if a pod does not exist.

        """
        pods = to_list(x)
        if len(pods) == 0:
            return
        full_cmd = self.docker_cmd + ["pod", "kill"]
        full_cmd.add_simple_arg("--signal", format_signal_arg(signal))
        full_cmd.extend([str(p) for p in pods])
        run(full_cmd)

    def list(
        self, *, filters: Union[Iterable[PodListFilter], Mapping[str, Any]] = ()
    ) -> List[Pod]:
        """List the pods on the host.

        Parameters:
            filters: Filters to apply when listing pods

        # Returns
            A `List[python_on_whales.Pod]`
        """
        if isinstance(filters, Mapping):
            filters = filters.items()
            warnings.warn(
                "Passing filters as a mapping is deprecated, replace with an "
                "iterable of tuples instead, as so:\n"
                f"filters={list(filters)}",
                DeprecationWarning,
            )
        full_cmd = self.docker_cmd + ["pod", "ps", "-q", "--no-trunc"]
        full_cmd.add_args_iterable("--filter", (f"{f[0]}={f[1]}" for f in filters))

        return [
            Pod(self.client_config, x, is_immutable_id=True)
            for x in run(full_cmd).splitlines()
        ]

    ps = list

    def logs(
        self,
        pod: ValidPod,
        container: Optional[
            python_on_whales.components.container.cli_wrapper.ValidContainer
        ] = None,
        *,
        names: bool = False,
        since: Union[None, datetime, timedelta] = None,
        tail: Optional[int] = None,
        timestamps: bool = False,
        until: Union[None, datetime, timedelta] = None,
        follow: bool = False,
        stream: bool = False,
    ) -> Union[str, Iterable[Tuple[str, bytes]]]:
        """Returns the logs of a pod's containers as a string or an iterator.

        Parameters:
            pod: The pod to get the container logs of
            container: Filter logs by container
            names: Output container names instead of IDs in the logs
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
                This function will then return an iterator that will yield a
                tuple `(source, content)` with `source` being `"stderr"` or
                `"stdout"`. `content` is the content of the line as bytes.
                Take a look at [the user guide](https://gabrieldemarmiesse.github.io/python-on-whales/user_guide/docker_run/#stream-the-output)
                to have an example of the output.

        # Returns
            `str` if `stream=False` (the default), `Iterable[Tuple[str, bytes]]`
            if `stream=True`.

        # Raises
            `python_on_whales.exceptions.NoSuchPod` if the container does not exist.

        If you are a bit confused about `follow` and `stream`, here are some use cases.

        * If you want to have the logs up to this point as a `str`, don't use those args.
        * If you want to stream the output in real time, use `follow=True, stream=True`
        * If you want the logs up to this point, but you don't want to fit all the logs
        in memory because they are too big, use `stream=True`.
        """

        # first we verify that the pod exists and raise an exception if not.
        self.inspect(pod)

        full_cmd = self.docker_cmd + ["pod", "logs"]
        full_cmd.add_simple_arg("--container", container)
        full_cmd.add_flag("--names", names)
        full_cmd.add_simple_arg("--since", format_time_arg(since))
        full_cmd.add_simple_arg("--tail", tail)
        full_cmd.add_flag("--timestamps", timestamps)
        full_cmd.add_simple_arg("--until", format_time_arg(until))
        full_cmd.add_flag("--follow", follow)
        full_cmd.append(pod)

        iterator = stream_stdout_and_stderr(full_cmd)

        if stream:
            return iterator
        else:
            return "".join(x[1].decode() for x in iterator)

    def pause(self, x: Union[ValidPod, Iterable[ValidPod]], /) -> None:
        """Pauses one or more pods

        Parameters:
            x: One or more pods to pause

        # Raises
            `python_on_whales.exceptions.NoSuchPod` if any pods does not exist.
        """
        pods = to_list(x)
        if len(pods) == 0:
            return
        full_cmd = self.docker_cmd + ["pod", "pause"]
        full_cmd.extend([str(p) for p in pods])
        run(full_cmd)

    def prune(self) -> None:
        """Remove pods that are not running."""
        full_cmd = self.docker_cmd + ["pod", "prune", "--force"]
        run(full_cmd)

    def remove(
        self,
        x: Union[ValidPod, Iterable[ValidPod]],
        /,
        *,
        force: bool = False,
        ignore: bool = False,
        time: Optional[int] = None,
    ):
        """Remove one or more pods.

        Parameters:
            x: Single pod or list of pods to remove.
            force: Force removal of the pods
            ignore: Ignore errors when specified pod is missing
            time: Seconds to wait for pod stop before killing the containers

        # Raises
            `python_on_whales.exceptions.NoSuchPod` if any of the pods do not
            exist and `ignore` was not set.

        """
        pods = to_list(x)
        if len(pods) == 0:
            return
        full_cmd = self.docker_cmd + ["pod", "rm"]
        full_cmd.add_flag("--force", force)
        full_cmd.add_flag("--ignore", ignore)
        full_cmd.add_simple_arg("--time", time)
        full_cmd.extend([str(p) for p in pods])
        run(full_cmd)

    def restart(self, x: Union[ValidPod, Iterable[ValidPod]], /) -> None:
        """Restarts one or more pods

        Parameters:
            x: One or more pods to restart

        # Raises
            `python_on_whales.exceptions.NoSuchPod` if any pods does not exist.
        """
        pods = to_list(x)
        if len(pods) == 0:
            return
        full_cmd = self.docker_cmd + ["pod", "restart"]
        full_cmd.extend([str(p) for p in pods])
        run(full_cmd)

    def start(self, x: Union[ValidPod, Iterable[ValidPod]], /) -> None:
        """Starts one or more pods

        Parameters:
            x: One or more pods to start

        # Raises
            `python_on_whales.exceptions.NoSuchPod` if any pods does not exist.
        """
        pods = to_list(x)
        if len(pods) == 0:
            return
        full_cmd = self.docker_cmd + ["pod", "start"]
        full_cmd.extend([str(p) for p in pods])
        run(full_cmd)

    def stats(self, x: Union[ValidPod, Iterable[ValidPod]], /) -> List[PodStats]:
        """Get pods resource usage statistics

        The data unit is the byte.

        Parameters:
            x: One or a list of pods

        # Returns
            A `List[python_on_whales.PodStats]`.
        """
        raise NotImplementedError  # TODO: implement PodStats class

        pods = to_list(x)
        if len(pods) == 0:
            return []
        full_cmd = self.docker_cmd + [
            "pod",
            "stats",
            "--format",
            "{{json .}}",
            "--no-stream",
        ]
        stats_output = run(full_cmd)
        return [PodStats(json.loads(s)) for s in stats_output.splitlines()]

    def stop(
        self,
        x: Union[ValidPod, Iterable[ValidPod]],
        /,
        *,
        time: Optional[int] = None,
    ) -> None:
        """Stops one or more pods

        Parameters:
            x: One or more pods to stop
            time: Seconds to wait for pods to stop before killing containers

        # Raises
            `python_on_whales.exceptions.NoSuchPod` if any pods does not exist.
        """
        pods = to_list(x)
        if len(pods) == 0:
            return
        full_cmd = self.docker_cmd + ["pod", "stop"]
        full_cmd.add_simple_arg("--time", time)
        full_cmd.extend([str(p) for p in pods])
        run(full_cmd)

    def top(self, pod: ValidPod):
        """Get the running processes of a pod

        Not yet implemented"""
        raise NotImplementedError

    def unpause(self, x: Union[ValidPod, Iterable[ValidPod]], /) -> None:
        """Unpauses one or more pods

        Parameters:
            x: One or more pods to unpause

        # Raises
            `python_on_whales.exceptions.NoSuchPod` if any pod do not exist.
        """
        pods = to_list(x)
        if len(pods) == 0:
            return
        full_cmd = self.docker_cmd + ["pod", "unpause"]
        full_cmd.extend([str(p) for p in pods])
        run(full_cmd)


class PodStats:
    def __init__(self, json_dict: Mapping[str, Any]):
        """Takes a json_dict with pod stats from the CLI and
        parses it.
        """
        # TODO: See ContainerStats class.

    def __repr__(self):
        attr = ", ".join(f"{key}={value}" for key, value in self.__dict__.items())
        return f"<{self.__class__} object, attributes are {attr}>"
