from datetime import datetime
from typing import Any, Dict, List, Union

from python_on_whales.client_config import (
    ClientConfig,
    DockerCLICaller,
    ReloadableObjectFromJson,
)
from python_on_whales.utils import DockerCamelModel, run, to_list


class NetworkInspectResult(DockerCamelModel):
    id: str
    name: str
    created: datetime
    scope: str
    driver: str
    enable_I_pv6: bool
    internal: bool
    attachable: bool
    ingress: bool
    config_from: dict
    config_only: bool
    containers: dict
    options: dict
    labels: dict


class Network(ReloadableObjectFromJson):
    def __init__(
        self, client_config: ClientConfig, reference: str, is_immutable_id=False
    ):
        super().__init__(client_config, "id", reference, is_immutable_id)

    def _fetch_inspect_result_json(self, reference):
        return run(self.docker_cmd + ["network", "inspect", reference])

    def _parse_json_object(self, json_object: Dict[str, Any]) -> NetworkInspectResult:
        return NetworkInspectResult.parse_obj(json_object)

    @property
    def id(self) -> str:
        return self._get_immutable_id()

    @property
    def name(self) -> List[str]:
        return self._get_inspect_result().name


ValidNetwork = Union[Network, str]


class NetworkCLI(DockerCLICaller):
    def create(self, name: str):
        full_cmd = self.docker_cmd + ["network", "create"]
        full_cmd.append(name)
        return Network(self.client_config, run(full_cmd), is_immutable_id=True)

    def remove(self, networks: Union[ValidNetwork, List[ValidNetwork]]):
        full_cmd = self.docker_cmd + ["network", "remove"]
        for network in to_list(networks):
            full_cmd.append(network)
        run(full_cmd)
