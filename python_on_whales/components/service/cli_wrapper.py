from __future__ import annotations

import json
import warnings
from datetime import datetime, timedelta
from typing import (
    Any,
    Dict,
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

import python_on_whales.components.task.cli_wrapper
from python_on_whales.client_config import (
    ClientConfig,
    DockerCLICaller,
    ReloadableObjectFromJson,
)
from python_on_whales.components.container.cli_wrapper import to_seconds
from python_on_whales.components.service.models import (
    ServiceEndpoint,
    ServiceInspectResult,
    ServiceSpec,
    ServiceUpdateStatus,
    ServiceVersion,
)
from python_on_whales.exceptions import NoSuchService
from python_on_whales.utils import (
    ValidPath,
    format_mapping_for_cli,
    format_time_arg,
    run,
    stream_stdout_and_stderr,
    to_list,
)

ServiceListFilter: TypeAlias = Union[
    Tuple[Literal["id"], str],
    Tuple[Literal["label"], str],
    Tuple[Literal["mode"], str],
    Tuple[Literal["name"], str],
]


class Service(ReloadableObjectFromJson):
    def __init__(
        self, client_config: ClientConfig, reference: str, is_immutable_id=False
    ):
        super().__init__(client_config, "id", reference, is_immutable_id)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.remove()

    def _fetch_inspect_result_json(self, reference):
        json_str = run(self.docker_cmd + ["service", "inspect", reference])
        return json.loads(json_str)[0]

    def _parse_json_object(self, json_object: Dict[str, Any]) -> ServiceInspectResult:
        return ServiceInspectResult(**json_object)

    def _get_inspect_result(self) -> ServiceInspectResult:
        """Only there to allow tools to know the return type"""
        return super()._get_inspect_result()

    @property
    def id(self) -> str:
        return self._get_immutable_id()

    @property
    def version(self) -> ServiceVersion:
        return self._get_inspect_result().version

    @property
    def created_at(self) -> datetime:
        return self._get_inspect_result().created_at

    @property
    def updated_at(self) -> datetime:
        return self._get_inspect_result().updated_at

    @property
    def spec(self) -> ServiceSpec:
        return self._get_inspect_result().spec

    @property
    def previous_spec(self) -> Optional[ServiceSpec]:
        return self._get_inspect_result().previous_spec

    @property
    def endpoint(self) -> ServiceEndpoint:
        return self._get_inspect_result().endpoint

    @property
    def update_status(self) -> Optional[ServiceUpdateStatus]:
        return self._get_inspect_result().update_status

    def ps(self) -> List[python_on_whales.components.task.cli_wrapper.Task]:
        """Returns the list of tasks of this service."""
        return ServiceCLI(self.client_config).ps(self)

    def remove(self) -> None:
        """Removes this service

        It's also possible to use a service as a context manager.
        By using a context manager, you ensures that the service will be removed even
        if an exception occurs.

        ```python
        from python_on_whales import docker

        docker.swarm.init()
        with docker.service.create("ubuntu", ["sleep", "infinity"]) as my_service:
            print("I'm doing things with the service here")
            print(my_service.update_status)

        print("I'm out of the context manager, the service has been removed.")
        ```
        """
        ServiceCLI(self.client_config).remove(self)

    def scale(self, new_scale: int, detach: bool = False) -> None:
        """Change the scale of a service.

        See the [`docker.service.scale`](../sub-commands/service.md#scale) command for
        information about the arguments.
        """
        ServiceCLI(self.client_config).scale({self: new_scale}, detach=detach)

    def update(
        self,
        detach: bool = False,
        force: bool = False,
        image: Optional[str] = None,
        with_registry_authentication: bool = False,
        quiet: bool = False,
        replicas: Optional[int] = None,
    ):
        """Updates a service

        See the [`docker.service.update`](../sub-commands/service.md#update) command for
        information about the arguments.
        """
        ServiceCLI(self.client_config).update(
            self, detach, force, image, with_registry_authentication, quiet, replicas
        )

    def exists(self) -> bool:
        """Returns `True` if the service is still present in the swarm, `False`
        if the service has been removed.
        """
        return ServiceCLI(self.client_config).exists(self.id)


ValidService = Union[str, Service]


class ServiceCLI(DockerCLICaller):
    def create(
        self,
        image: str,
        command: Optional[List[str]],
        cap_add: List[str] = [],
        cap_drop: List[str] = [],
        constraints: List[str] = [],
        detach: bool = False,
        dns: List[str] = [],
        dns_options: List[str] = [],
        dns_search: List[str] = [],
        endpoint_mode: Optional[str] = None,
        entrypoint: Optional[str] = None,
        envs: Dict[str, str] = {},
        env_files: Union[ValidPath, List[ValidPath]] = [],
        generic_resources: List[str] = [],
        groups: List[str] = [],
        healthcheck: bool = True,
        health_cmd: Optional[str] = None,
        health_interval: Union[None, int, timedelta] = None,
        health_retries: Optional[int] = None,
        health_start_period: Union[None, int, timedelta] = None,
        health_timeout: Union[None, int, timedelta] = None,
        hosts: Dict[str, str] = {},
        hostname: Optional[str] = None,
        init: bool = False,
        isolation: Optional[str] = None,
        labels: Dict[str, str] = {},
        limit_cpu: Optional[float] = None,
        limit_memory: Optional[str] = None,
        limit_pids: Optional[int] = None,
        log_driver: Optional[str] = None,
        network: Optional[str] = None,
        restart_condition: Optional[Literal["none", "on-failure", "any"]] = None,
        restart_max_attempts: Optional[int] = None,
        secrets: Optional[List[Dict[str, str]]] = [],
        mounts: Optional[List[Dict[str, str]]] = [],
    ):
        """Creates a Docker swarm service.

        Consider using 'docker stack deploy' instead as it's idempotent and
        easier to read for complex applications.
        docker stack deploy is basically docker compose for swarm clusters.

        Parameters:
            image: The image to use as the base for the service.
            command: The command to execute in the container(s).
        """
        full_cmd = self.docker_cmd + ["service", "create", "--quiet"]

        full_cmd.add_args_iterable_or_single("--cap-add", cap_add)
        full_cmd.add_args_iterable_or_single("--cap-drop", cap_drop)
        full_cmd.add_args_iterable_or_single("--constraint", constraints)

        full_cmd.add_flag("--detach", detach)
        full_cmd.add_args_iterable_or_single("--dns", dns)
        full_cmd.add_args_iterable_or_single("--dns-option", dns_options)
        full_cmd.add_args_iterable_or_single("--dns-search", dns_search)
        full_cmd.add_simple_arg("--endpoint-mode", endpoint_mode)
        full_cmd.add_simple_arg("--entrypoint", entrypoint)

        full_cmd.add_args_iterable_or_single("--env", format_mapping_for_cli(envs))
        full_cmd.add_args_iterable_or_single("--env-file", env_files)

        full_cmd.add_args_iterable_or_single("--generic-resource", generic_resources)
        full_cmd.add_args_iterable_or_single("--group", groups)

        full_cmd.add_flag("--no-healthcheck", not healthcheck)
        full_cmd.add_simple_arg("--health-cmd", health_cmd)
        full_cmd.add_simple_arg("--health-interval", to_seconds(health_interval))
        full_cmd.add_simple_arg("--health-retries", health_retries)
        full_cmd.add_simple_arg(
            "--health-start-period", to_seconds(health_start_period)
        )
        full_cmd.add_simple_arg("--health-timeout", to_seconds(health_timeout))
        for key, value in hosts:
            full_cmd += ["--host", f"{key}:{value}"]

        full_cmd.add_simple_arg("--hostname", hostname)

        full_cmd.add_flag("--init", init)
        full_cmd.add_simple_arg("--isolation", isolation)
        full_cmd.add_args_iterable_or_single("--label", format_mapping_for_cli(labels))
        full_cmd.add_simple_arg("--limit-cpu", limit_cpu)
        full_cmd.add_simple_arg("--limit-memory", limit_memory)
        full_cmd.add_simple_arg("--limit-pids", limit_pids)
        full_cmd.add_simple_arg("--log-driver", log_driver)
        full_cmd.add_simple_arg("--restart-condition", restart_condition)
        full_cmd.add_simple_arg("--restart-max-attempts", restart_max_attempts)
        full_cmd.add_args_iterable_or_single(
            "--mount", [",".join(format_mapping_for_cli(s)) for s in mounts or []]
        )
        full_cmd.add_simple_arg("--network", network)
        full_cmd.add_args_iterable_or_single(
            "--secret", [",".join(format_mapping_for_cli(s)) for s in secrets or []]
        )

        full_cmd.append(image)
        if command is not None:
            for string in to_list(command):
                full_cmd.append(string)

        service_id = run(full_cmd)
        return Service(self.client_config, service_id, is_immutable_id=True)

    @overload
    def inspect(self, x: str) -> Service:
        pass

    @overload
    def inspect(self, x: List[str]) -> List[Service]: ...

    def inspect(self, x: Union[str, List[str]]) -> Union[Service, List[Service]]:
        """Returns one or a list of `python_on_whales.Service` object(s).

        # Raises
            `python_on_whales.exceptions.NoSuchService` if one of the services
            doesn't exists.
        """
        if isinstance(x, str):
            return Service(self.client_config, x)
        else:
            return [Service(self.client_config, a) for a in x]

    def exists(self, x: str) -> bool:
        """Verify that a service exists.

         It's just calling `docker.service.inspect(...)` and verifies that it doesn't throw
         a `python_on_whales.exceptions.NoSuchService`.

        # Returns
            A `bool`
        """
        try:
            self.inspect(x)
        except NoSuchService:
            return False
        else:
            return True

    def logs(
        self,
        service: ValidService,
        details: bool = False,
        since: Union[None, datetime, timedelta] = None,
        tail: Optional[int] = None,
        timestamps: bool = False,
        follow: bool = False,
        raw: bool = False,
        task_ids: bool = True,
        resolve: bool = True,
        truncate: bool = True,
        stream: bool = False,
    ):
        """Returns the logs of a service as a string or an iterator.

        Parameters:
            service: The service to get the logs of
            details: Show extra details provided to logs
            since: Use a datetime or timedelta to specify the lower
                date limit for the logs.
            tail: Number of lines to show from the end of the logs (default all)
            timestamps: Put timestamps next to lines.
            follow: If `False` (the default), the logs returned are the logs up to the time
                of the function call. If `True`, the logs of the container up to the time the
                service is stopped (removed) are displayed.
                Which is why you must use the `stream` option if you use the `follow` option.
                Without `stream`, only a `str` will be returned, possibly much later in the
                future (maybe never if the service is never removed). So this option is not
                possible (You'll get an error if you use follow and not stream).
                With `stream`, you'll be able to read the logs in real time and stop
                whenever you need.
            stream: Similar to the `stream` argument of `docker.run()`.
                This function will then returns and iterator that will yield a
                tuple `(source, content)` with `source` being `"stderr"` or
                `"stdout"`. `content` is the content of the line as bytes.
                Take a look at [the user guide](https://gabrieldemarmiesse.github.io/python-on-whales/user_guide/docker_run/#stream-the-output)
                to have an example of the output.

        # Returns
            `str` if `stream=False` (the default), `Iterable[Tuple[str, bytes]]`
            if `stream=True`.

        # Raises
            `python_on_whales.exceptions.NoSuchService` if the service does not exists.
        """
        # first we verify that the service exists and raise an exception if not.
        self.inspect(str(service))

        full_cmd = self.docker_cmd + ["service", "logs"]
        full_cmd.add_flag("--details", details)
        full_cmd.add_simple_arg("--since", format_time_arg(since))
        full_cmd.add_simple_arg("--tail", tail)
        full_cmd.add_flag("--timestamps", timestamps)
        full_cmd.add_flag("--follow", follow)
        full_cmd.add_flag("--raw", raw)
        full_cmd.add_flag("--no-task-ids", not task_ids)
        full_cmd.add_flag("--no-resolve", not resolve)
        full_cmd.add_flag("--no-trunc", not truncate)
        full_cmd.append(service)

        iterator = stream_stdout_and_stderr(full_cmd)
        if stream:
            return iterator
        else:
            return "".join(x[1].decode() for x in iterator)

    def list(
        self, filters: Union[Iterable[ServiceListFilter], Mapping[str, Any]] = ()
    ) -> List[Service]:
        """Returns the list of services

        Parameters:
            filters: If you want to filter the results based on a given condition.
                For example, `docker.service.list(filters=dict(label="my_label=hello"))`.

        # Returns
            A `List[python_on_whales.Services]`
        """
        if isinstance(filters, Mapping):
            filters = filters.items()
            warnings.warn(
                "Passing filters as a mapping is deprecated, replace with an "
                "iterable of tuples instead, as so:\n"
                f"filters={list(filters)}",
                DeprecationWarning,
            )
        full_cmd = self.docker_cmd + ["service", "list", "--quiet"]
        full_cmd.add_args_iterable("--filter", (f"{f[0]}={f[1]}" for f in filters))

        ids_truncated = run(full_cmd).splitlines()

        # the ids are truncated because there is no single docker command that allows us to get them
        # untruncated. We must run an inspect command to get all untruncated ids.

        if ids_truncated == []:
            return []

        full_cmd = (
            self.docker_cmd
            + ["service", "inspect"]
            + ids_truncated
            + ["--format", "{{.ID}}"]
        )
        ids_not_truncated = run(full_cmd).splitlines()

        return [
            Service(self.client_config, x, is_immutable_id=True)
            for x in ids_not_truncated
        ]

    def ps(
        self, x: Union[ValidService, List[ValidService]]
    ) -> List[python_on_whales.components.task.cli_wrapper.Task]:
        """Returns the list of swarm tasks associated with this service.

        You can pass multiple services at once at this function.

        ```python
        from python_on_whales import docker

        tasks = docker.service.ps("my-service-name")
        print(tasks[0].desired_state)
        # running
        ```

        Parameters:
            x: One or more services (can be id, name or `python_on_whales.Service` object.)

        # Returns
            `List[python_on_whales.Task]`

        # Raises
            `python_on_whales.exceptions.NoSuchService` if one of the services
            doesn't exist.
        """
        full_cmd = (
            self.docker_cmd + ["service", "ps", "--quiet", "--no-trunc"] + to_list(x)
        )
        ids = run(full_cmd).splitlines()
        return [
            python_on_whales.components.task.cli_wrapper.Task(
                self.client_config, id_, is_immutable_id=True
            )
            for id_ in ids
        ]

    def remove(self, services: Union[ValidService, List[ValidService]]) -> None:
        """Removes a service

        Parameters:
            services: One or a list of services to remove.

        # Raises
            `python_on_whales.exceptions.NoSuchService` if one of the services
            doesn't exist.
        """
        full_cmd = self.docker_cmd + ["service", "remove"]

        if services == []:
            return

        for service in to_list(services):
            full_cmd.append(service)

        run(full_cmd)

    def rollback(self):
        """Not yet implemented"""
        raise NotImplementedError

    def scale(self, new_scales: Dict[ValidService, int], detach: bool = False) -> None:
        """Scale one or more services.

        Parameters:
            new_scales: Mapping between services and the desired scales. For example
                you can provide `new_scale={"service1": 4, "service2": 8}`
            detach: If True, does not wait for the services to converge and return
                immediately.

        # Raises
            `python_on_whales.exceptions.NoSuchService` if one of the services
            doesn't exists.

        """
        # verify that the services exists
        self.inspect(list(new_scales.keys()))

        full_cmd = self.docker_cmd + ["service", "scale"]
        full_cmd.add_flag("--detach", detach)
        for service, new_scale in new_scales.items():
            full_cmd.append(f"{str(service)}={new_scale}")
        run(full_cmd, capture_stderr=False, capture_stdout=False)

    def update(
        self,
        service: ValidService,
        detach: bool = False,
        force: bool = False,
        image: Optional[str] = None,
        with_registry_authentication: bool = False,
        quiet: bool = False,
        replicas: Optional[int] = None,
    ):
        """Update a service

        More options coming soon

        Parameters:
            service: The service to update
            detach: Exit immediately instead of waiting for the service to converge
            force: Force update even if no changes require it
            image: Service image tag
            with_registry_authentication: Send registry authentication details
                to swarm agents

        # Raises
            `python_on_whales.exceptions.NoSuchService` if the service doesn't exists.
        """
        full_cmd = self.docker_cmd + ["service", "update"]
        full_cmd.add_flag("--force", force)
        full_cmd.add_simple_arg("--image", image)
        full_cmd.add_flag("--with-registry-auth", with_registry_authentication)
        full_cmd.add_flag("--detach", detach)
        full_cmd.add_flag("--quiet", quiet)
        full_cmd.add_simple_arg("--replicas", replicas)
        full_cmd.append(service)
        run(full_cmd, capture_stdout=False)
