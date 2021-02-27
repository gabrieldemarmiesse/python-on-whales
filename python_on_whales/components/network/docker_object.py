from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Union

import python_on_whales.components.network.cli_wrapper
from python_on_whales.client_config import ClientConfig, ReloadableObjectFromJson
from python_on_whales.components.network.models import (
    NetworkContainer,
    NetworkInspectResult,
    NetworkIPAM,
)
from python_on_whales.utils import run


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
        python_on_whales.components.network.cli_wrapper.NetworkCLI(
            self.client_config
        ).remove(self)


ValidNetwork = Union[Network, str]
