from datetime import datetime
from typing import Any, Dict, List, Tuple, Union

import python_on_whales.components.image
from python_on_whales.client_config import (
    ClientConfig,
    DockerCLICaller,
    ReloadableObjectFromJson,
)
from python_on_whales.utils import DockerCamelModel, run, to_list


class ServiceInspectResult(DockerCamelModel):
    ID: str
    version: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    spec: dict


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
    def spec(self) -> dict:
        return self._get_inspect_result().spec


ValidService = Union[str, Service]


class ServiceCLI(DockerCLICaller):
    def create(
        self,
        image: str,
        command: Union[str, List[str], None],
    ):
        """Creates a Docker swarm service.

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

    def remove(self, services: Union[ValidService, List[ValidService]]):
        """Removes a service

        # Arguments
            services: One or a list of services to remove.
        """
        full_cmd = self.docker_cmd + ["service", "remove"]

        for service in to_list(services):
            full_cmd.append(service)

        run(full_cmd)

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

    def list(self) -> List[Service]:
        """Returns the list of services

        # Returns
            A `List[python_on_whales.Services]`
        """
        full_cmd = self.docker_cmd + ["service", "list", "--quiet"]

        ids = run(full_cmd).splitlines()

        return [Service(self.client_config, x) for x in ids]
