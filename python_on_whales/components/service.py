from datetime import datetime
from typing import Any, Dict, List, Optional, Union, overload

from python_on_whales.client_config import (
    ClientConfig,
    DockerCLICaller,
    ReloadableObjectFromJson,
)
from python_on_whales.utils import DockerCamelModel, run, to_list


class Resources(DockerCamelModel):
    limits: Dict[str, int]
    reservations: Dict[str, int]


class ContainerSpec(DockerCamelModel):
    image: str
    labels: Dict[str, str]
    privileges: Dict[str, Optional[str]]
    stop_grace_period: int
    isolation: str
    env: Optional[List[str]]


class TaskTemplate(DockerCamelModel):
    container_spec: ContainerSpec
    resources: Resources


class ChangeConfig(DockerCamelModel):
    parallelism: int
    failure_action: str
    monitor: int
    max_failure_ratio: int
    order: str


class ServiceSpec(DockerCamelModel):
    name: str
    labels: Dict[str, str]
    mode: Dict[str, Any]
    update_config: ChangeConfig
    rollback_config: ChangeConfig
    task_template: TaskTemplate


class ServiceInspectResult(DockerCamelModel):
    ID: str
    version: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    spec: ServiceSpec


class Service(ReloadableObjectFromJson):
    def __init__(
        self, client_config: ClientConfig, reference: str, is_immutable_id=False
    ):
        super().__init__(client_config, "ID", reference, is_immutable_id)

    def _fetch_inspect_result_json(self, reference):
        return run(self.docker_cmd + ["service", "inspect", reference])

    def _parse_json_object(self, json_object: Dict[str, Any]) -> ServiceInspectResult:
        return ServiceInspectResult.parse_obj(json_object)

    @property
    def id(self) -> str:
        return self._get_immutable_id()

    @property
    def version(self) -> Dict[str, Any]:
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


ValidService = Union[str, Service]


class ServiceCLI(DockerCLICaller):
    def create(
        self,
        image: str,
        command: Union[str, List[str], None],
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

    def ps(self):
        """Not yet implemented"""
        raise NotImplementedError

    def remove(self, services: Union[ValidService, List[ValidService]]):
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

    def scale(self, new_scales: Dict[ValidService, int], detach=False):
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
        """Update a service"""
        full_cmd = self.docker_cmd + ["service", "update"]
        full_cmd.add_flag("--force", force)
        full_cmd.add_simple_arg("--image", image)
        full_cmd.add_flag("--with-registry-auth", with_registry_authentication)
        full_cmd.add_flag("--detach", detach)
        full_cmd.append(service)
        run(full_cmd, capture_stdout=False)
