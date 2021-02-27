from typing import Dict, List, Optional, Union, overload

import python_on_whales.components.container
from python_on_whales.client_config import DockerCLICaller
from python_on_whales.components.network.docker_object import Network, ValidNetwork
from python_on_whales.utils import format_dict_for_cli, run, to_list


class NetworkCLI(DockerCLICaller):
    def connect(
        self,
        network: ValidNetwork,
        container: python_on_whales.components.container.ValidContainer,
        alias: Optional[str] = None,
        driver_options: List[str] = [],
        ip: Optional[str] = None,
        ip6: Optional[str] = None,
        links: List[python_on_whales.components.container.ValidContainer] = [],
    ) -> None:
        full_cmd = self.docker_cmd + ["network", "connect"]
        full_cmd.add_simple_arg("--alias", alias)
        full_cmd.add_args_list("--driver-opt", driver_options)
        full_cmd.add_simple_arg("--ip", ip)
        full_cmd.add_simple_arg("--ip6", ip6)
        full_cmd.add_args_list("--link", links)
        full_cmd += [network, container]
        run(full_cmd)

    def create(
        self,
        name: str,
        attachable: bool = False,
        driver: Optional[str] = None,
        gateway: Optional[str] = None,
        subnet: Optional[str] = None,
        options: List[str] = [],
    ) -> Network:
        """Creates a Docker network.

        # Arguments
            name: The name of the network

        # Returns
            A `python_on_whales.Network`.
        """
        full_cmd = self.docker_cmd + ["network", "create"]
        full_cmd.add_flag("--attachable", attachable)
        full_cmd.add_simple_arg("--driver", driver)
        full_cmd.add_simple_arg("--gateway", gateway)
        full_cmd.add_simple_arg("--subnet", subnet)
        full_cmd.add_args_list("--opt", options)
        full_cmd.append(name)
        return Network(self.client_config, run(full_cmd), is_immutable_id=True)

    def disconnect(
        self,
        network: ValidNetwork,
        container: python_on_whales.components.container.ValidContainer,
        force: bool = False,
    ):
        full_cmd = self.docker_cmd + ["network", "disconnet"]
        full_cmd.add_flag("--force", force)
        full_cmd += [network, container]
        run(full_cmd)

    @overload
    def inspect(self, x: str) -> Network:
        ...

    @overload
    def inspect(self, x: List[str]) -> List[Network]:
        ...

    def inspect(self, x: Union[str, List[str]]) -> Union[Network, List[Network]]:
        if isinstance(x, str):
            return Network(self.client_config, x)
        else:
            return [Network(self.client_config, reference) for reference in x]

    def list(self, filters: Dict[str, str] = {}) -> List[Network]:
        full_cmd = self.docker_cmd + ["network", "list", "--no-trunc", "--quiet"]
        full_cmd.add_args_list("--filter", format_dict_for_cli(filters))

        ids = run(full_cmd).splitlines()
        return [Network(self.client_config, id_, is_immutable_id=True) for id_ in ids]

    def prune(self, filters: Dict[str, str] = {}):
        full_cmd = self.docker_cmd + ["network", "prune", "--force"]
        full_cmd.add_args_list("--filter", format_dict_for_cli(filters))
        run(full_cmd)

    def remove(self, networks: Union[ValidNetwork, List[ValidNetwork]]):
        """Removes a Docker network

        # Arguments
            networks: One or more networks.
        """
        full_cmd = self.docker_cmd + ["network", "remove"]
        for network in to_list(networks):
            full_cmd.append(network)
        run(full_cmd)
