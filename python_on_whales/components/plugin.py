from __future__ import annotations

from typing import Any, Dict

from python_on_whales.client_config import (
    ClientConfig,
    DockerCLICaller,
    ReloadableObjectFromJson,
)
from python_on_whales.utils import DockerCamelModel, run


class PluginInspectResult(DockerCamelModel):
    id: str
    name: str


class Plugin(ReloadableObjectFromJson):
    def __init__(
        self, client_config: ClientConfig, reference: str, is_immutable_id=False
    ):
        super().__init__(client_config, "id", reference, is_immutable_id)

    def _fetch_inspect_result_json(self, reference):
        return run(self.docker_cmd + ["node", "inspect", reference])

    def _parse_json_object(self, json_object: Dict[str, Any]) -> PluginInspectResult:
        return PluginInspectResult.parse_obj(json_object)

    def _get_inspect_result(self) -> PluginInspectResult:
        """Only there to allow tools to know the return type"""
        return super()._get_inspect_result()

    @property
    def id(self) -> str:
        return self._get_immutable_id()

    @property
    def name(self) -> str:
        return self._get_inspect_result().name

    def disable(self):
        """Not yet implemented"""
        raise NotImplementedError

    def enable(self):
        """Not yet implemented"""
        raise NotImplementedError

    def push(self):
        """Not yet implemented"""
        raise NotImplementedError

    def remove(self):
        """Not yet implemented"""
        raise NotImplementedError

    def set(self):
        """Not yet implemented"""
        raise NotImplementedError

    def upgrade(self):
        """Not yet implemented"""
        raise NotImplementedError


class PluginCLI(DockerCLICaller):
    def create(self):
        """Not yet implemented"""
        raise NotImplementedError

    def disable(self):
        """Not yet implemented"""
        raise NotImplementedError

    def enable(self):
        """Not yet implemented"""
        raise NotImplementedError

    def inspect(self):
        """Not yet implemented"""
        raise NotImplementedError

    def install(self):
        """Not yet implemented"""
        raise NotImplementedError

    def list(self):
        """Not yet implemented"""
        raise NotImplementedError

    def push(self):
        """Not yet implemented"""
        raise NotImplementedError

    def remove(self):
        """Not yet implemented"""
        raise NotImplementedError

    def set(self):
        """Not yet implemented"""
        raise NotImplementedError

    def upgrade(self):
        """Not yet implemented"""
        raise NotImplementedError
