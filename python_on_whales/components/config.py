from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, overload

import pydantic

from python_on_whales.client_config import (
    ClientConfig,
    DockerCLICaller,
    ReloadableObjectFromJson,
)
from python_on_whales.utils import DockerCamelModel, format_dict_for_cli, run, to_list


class DockerObjectVersion(DockerCamelModel):
    index: int


class ConfigSpecDriver(DockerCamelModel):
    name: str
    options: Dict[str, Any]


class ConfigSpec(DockerCamelModel):
    name: str
    labels: Dict[str, str]
    data: str
    templating: ConfigSpecDriver


class ConfigInspectResult(DockerCamelModel):
    id: str = pydantic.Field(alias="ID")
    version: DockerObjectVersion
    created_at: datetime
    updated_at: datetime
    spec: ConfigSpec


class Config(ReloadableObjectFromJson):
    def __init__(
        self, client_config: ClientConfig, reference: str, is_immutable_id=False
    ):
        super().__init__(client_config, "ID", reference, is_immutable_id)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.remove()

    def _fetch_inspect_result_json(self, reference):
        return run(self.docker_cmd + ["config", "inspect", reference])

    def _parse_json_object(self, json_object: Dict[str, Any]):
        return ConfigInspectResult.parse_obj(json_object)

    def remove(self):
        ConfigCLI(self.client_config).remove(self)


ValidConfig = Union[Config, str]


class ConfigCLI(DockerCLICaller):
    def create(
        self,
        name: str,
        file: Union[str, Path],
        labels: Dict[str, str] = {},
        template_driver: Optional[str] = None,
    ) -> Config:
        """Not yet implemented"""
        full_cmd = self.docker_cmd + ["config", "create"]
        full_cmd.add_args_list("--label", format_dict_for_cli(labels))
        full_cmd.add_simple_arg("--template-driver", template_driver)
        full_cmd += [name, file]
        return Config(self.client_config, run(full_cmd), is_immutable_id=True)

    @overload
    def inspect(self, x: str) -> Config:
        ...

    @overload
    def inspect(self, x: List[str]) -> List[Config]:
        ...

    def inspect(self, x: Union[str, List[str]]) -> Union[Config, List[Config]]:
        """Not yet implemented"""
        if isinstance(x, str):
            return Config(self.client_config, x)
        else:
            return [Config(self.client_config, reference) for reference in x]

    def list(self, filters: Dict[str, str] = {}) -> List[Config]:
        """Not yet implemented"""
        full_cmd = self.docker_cmd + ["config", "list", "--quiet"]
        full_cmd.add_args_list("--filter", format_dict_for_cli(filters))
        output = run(full_cmd)
        ids = output.splitlines()
        return [Config(self.client_config, id_, is_immutable_id=True) for id_ in ids]

    def remove(self, x: Union[ValidConfig, List[ValidConfig]]):
        """Remove one or more config.

        # Arguments
            x: One or a list of configs. Valid values are the id of the config or
                a `python_on_whales.Config` object.
        """
        full_cmd = self.docker_cmd + ["config", "rm"]
        full_cmd += to_list(x)
        run(full_cmd)
