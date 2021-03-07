from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Union, overload

import python_on_whales.components.container.cli_wrapper
from python_on_whales.client_config import (
    ClientConfig,
    DockerCLICaller,
    ReloadableObjectFromJson,
)
from python_on_whales.components.network.models import (
    NetworkContainer,
    NetworkInspectResult,
    NetworkIPAM,
)
from python_on_whales.utils import format_dict_for_cli, run, to_list


class Network(ReloadableObjectFromJson):
    def __init__(
        self, client_config: ClientConfig, reference: str, is_immutable_id=False
    ):
        super().__init__(client_config, "id", reference, is_immutable_id)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.remove()

    def _fetch_inspect_result_json(self, reference):
        return run(self.docker_cmd + ["network", "inspect", reference])

    def _parse_json_object(self, json_object: Dict[str, Any]) -> NetworkInspectResult:
        return NetworkInspectResult.parse_obj(json_object)

    def _get_inspect_result(self) -> NetworkInspectResult:
        """Only there to allow tools to know the return type"""
        return super()._get_inspect_result()

    @property
    def name(self) -> str:
        return self._get_inspect_result().name

    @property
    def id(self) -> str:
        return self._get_immutable_id()

    @property
    def created(self) -> datetime:
        return self._get_inspect_result().created

    @property
    def scope(self) -> str:
        return self._get_inspect_result().scope

    @property
    def driver(self) -> str:
        return self._get_inspect_result().driver

    @property
    def enable_ipv6(self) -> bool:
        return self._get_inspect_result().enable_ipv6

    @property
    def ipam(self) -> NetworkIPAM:
        return self._get_inspect_result().ipam

    @property
    def internal(self) -> bool:
        return self._get_inspect_result().internal

    @property
    def attachable(self) -> bool:
        return self._get_inspect_result().attachable

    @property
    def ingress(self) -> bool:
        return self._get_inspect_result().ingress

    @property
    def containers(self) -> Dict[str, NetworkContainer]:
        return self._get_inspect_result().containers

    @property
    def options(self) -> Dict[str, Any]:
        return self._get_inspect_result().options

    @property
    def labels(self) -> Dict[str, str]:
        return self._get_inspect_result().labels

    @property
    def config_from(self) -> dict:
        return self._get_inspect_result().config_from

    @property
    def config_only(self) -> bool:
        return self._get_inspect_result().config_only

    def remove(self) -> None:
        """Removes this Docker network.

        Rather than removing it manually, you can use a context manager to
        make sure the network is deleted even if an exception is raised.

        ```python
        from python_on_whales import docker

        with docker.network.create("some_name") as my_net:
            docker.run(
                "busybox",
                ["ping", "idonotexistatall.com"],
                networks=[my_net],
                remove=True,
            )
            # an exception will be raised because the container will fail
            # but the network will be removed anyway.
        ```

        """
        NetworkCLI(self.client_config).remove(self)


ValidNetwork = Union[Network, str]


class NetworkCLI(DockerCLICaller):
    def connect(
        self,
        network: ValidNetwork,
        container: python_on_whales.components.container.cli_wrapper.ValidContainer,
        alias: Optional[str] = None,
        driver_options: List[str] = [],
        ip: Optional[str] = None,
        ip6: Optional[str] = None,
        links: List[
            python_on_whales.components.container.cli_wrapper.ValidContainer
        ] = [],
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
        container: python_on_whales.components.container.cli_wrapper.ValidContainer,
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
