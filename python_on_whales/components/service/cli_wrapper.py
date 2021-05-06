from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, overload

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
from python_on_whales.utils import ValidPath, format_dict_for_cli, run, to_list


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
        return run(self.docker_cmd + ["service", "inspect", reference])

    def _parse_json_object(self, json_object: Dict[str, Any]) -> ServiceInspectResult:
        return ServiceInspectResult.parse_obj(json_object)

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
    ):
        """Updates a service

        See the [`docker.service.update`](../sub-commands/service.md#update) command for
        information about the arguments.
        """
        ServiceCLI(self.client_config).update(
            self, detach, force, image, with_registry_authentication
        )

    def exists(self) -> bool:
        """Returns `True` if the service is still present in the swarm, `False`
        if the service has been removed.
        """
        return self in ServiceCLI(self.client_config).list()


ValidService = Union[str, Service]


class ServiceCLI(DockerCLICaller):
    def create(
        self,
        image: str,
        command: Union[str, List[str], None],
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
    ):
        """Creates a Docker swarm service.

        Consider using 'docker stack deploy' instead as it's idempotent and
        easier to read for complex applications.
        docker stack deploy is basically docker compose for swarm clusters.

        # Arguments:
            image: The image to use as the base for the service.
            command: The command to execute in the container(s).
        """
        full_cmd = self.docker_cmd + ["service", "create", "--quiet"]

        full_cmd.add_args_list("--cap-add", cap_add)
        full_cmd.add_args_list("--cap-drop", cap_drop)
        full_cmd.add_args_list("--constraint", constraints)

        full_cmd.add_flag("--detach", detach)
        full_cmd.add_args_list("--dns", dns)
        full_cmd.add_args_list("--dns-option", dns_options)
        full_cmd.add_args_list("--dns-search", dns_search)
        full_cmd.add_simple_arg("--endpoint-mode", endpoint_mode)
        full_cmd.add_simple_arg("--entrypoint", entrypoint)

        full_cmd.add_args_list("--env", format_dict_for_cli(envs))
        full_cmd.add_args_list("--env-file", env_files)

        full_cmd.add_args_list("--generic-resource", generic_resources)
        full_cmd.add_args_list("--group", groups)

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
        full_cmd.add_args_list("--label", format_dict_for_cli(labels))
        full_cmd.add_simple_arg("--limit-cpu", limit_cpu)
        full_cmd.add_simple_arg("--limit-memory", limit_memory)
        full_cmd.add_simple_arg("--limit-pids", limit_pids)
        full_cmd.add_simple_arg("--log-driver", log_driver)

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
    def inspect(self, x: List[str]) -> List[Service]:
        ...

    def inspect(self, x: Union[str, List[str]]) -> Union[Service, List[Service]]:
        """Returns one or a list of `python_on_whales.Service` object(s)."""
        if isinstance(x, str):
            return Service(self.client_config, x)
        else:
            return [Service(self.client_config, a) for a in x]

    def logs(self):
        """Not yet implemented"""
        raise NotImplementedError

    def list(self) -> List[Service]:
        """Returns the list of services

        # Returns
            A `List[python_on_whales.Services]`
        """
        full_cmd = self.docker_cmd + ["service", "list", "--quiet"]

        ids = run(full_cmd).splitlines()

        return [Service(self.client_config, x) for x in ids]

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

        # Arguments
            x: One or more services (can be id, name or `python_on_whales.Service` object.)

        # Returns
            `List[python_on_whales.Task]`
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

        # Arguments
            services: One or a list of services to remove.
        """
        full_cmd = self.docker_cmd + ["service", "remove"]

        for service in to_list(services):
            full_cmd.append(service)

        run(full_cmd)

    def rollback(self):
        """Not yet implemented"""
        raise NotImplementedError

    def scale(self, new_scales: Dict[ValidService, int], detach: bool = False) -> None:
        """Scale one or more services.

        # Arguments
            new_scales: Mapping between services and the desired scales. For example
                you can provide `new_scale={"service1": 4, "service2": 8}`
            detach: If True, does not wait for the services to converge and return
                immediately.
        """

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
    ):
        """Update a service

        More options coming soon

        # Arguments
            service: The service to update
            detach: Exit immediately instead of waiting for the service to converge
            force: Force update even if no changes require it
            image: Service image tag
            with_registry_authentication: Send registry authentication details
                to swarm agents
        """
        full_cmd = self.docker_cmd + ["service", "update"]
        full_cmd.add_flag("--force", force)
        full_cmd.add_simple_arg("--image", image)
        full_cmd.add_flag("--with-registry-auth", with_registry_authentication)
        full_cmd.add_flag("--detach", detach)
        full_cmd.append(service)
        run(full_cmd, capture_stdout=False)
