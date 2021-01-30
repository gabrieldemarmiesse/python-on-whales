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
    templating: Optional[ConfigSpecDriver]


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
        super().__init__(client_config, "id", reference, is_immutable_id)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.remove()

    def _fetch_inspect_result_json(self, reference):
        return run(self.docker_cmd + ["config", "inspect", reference])

    def _parse_json_object(self, json_object: Dict[str, Any]):
        return ConfigInspectResult.parse_obj(json_object)

    def _get_inspect_result(self) -> ConfigInspectResult:
        """Only there to allow tools to know the return type"""
        return super()._get_inspect_result()

    def remove(self):
        """Remove this config.

        Note that you can also use a `python_on_whales.Config` as a context manager
        to ensure it's removed even if an exception occurs.
        """
        ConfigCLI(self.client_config).remove(self)

    @property
    def id(self) -> str:
        return self._get_immutable_id()

    @property
    def version(self) -> DockerObjectVersion:
        return self._get_inspect_result().version

    @property
    def created_at(self) -> datetime:
        return self._get_inspect_result().created_at

    @property
    def updated_at(self) -> datetime:
        return self._get_inspect_result().updated_at

    @property
    def spec(self) -> ConfigSpec:
        return self._get_inspect_result().spec


ValidConfig = Union[Config, str]


class ConfigCLI(DockerCLICaller):
    def create(
        self,
        name: str,
        file: Union[str, Path],
        labels: Dict[str, str] = {},
        template_driver: Optional[str] = None,
    ) -> Config:
        """Create a config from a file

        See [the docker docs](https://docs.docker.com/engine/swarm/configs/)
        for more information about swarm configs.

        # Arguments
            name: The config name.
            file: Tbe file to be used as config.
            labels: The labels to add to the config
            template_driver: The template driver

        # Returns
            A `python_on_whales.Config` object.
        """
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
        """Returns a `python_on_whales.Config` object based on its name or id.

        # Argument
            x: An id or name or a list of ids/names.

        # Returns
            A `python_on_whales.Config` if a string was passed as argument. A
            `List[python_on_whales.Config]` if a list of strings was passed as argument.
        """
        if isinstance(x, str):
            return Config(self.client_config, x)
        else:
            return [Config(self.client_config, reference) for reference in x]

    def list(self, filters: Dict[str, str] = {}) -> List[Config]:
        """List all config available in the swarm.

        # Arguments
            filters: If you want to filter the results based on a given condition.
                For example, `docker.config.list(filters=dict(label="my_label=hello"))`.

        # Returns
            A `List[python_on_whales.Config]`.
        """
        full_cmd = self.docker_cmd + ["config", "list", "--quiet"]
        full_cmd.add_args_list("--filter", format_dict_for_cli(filters))
        output = run(full_cmd)
        ids = output.splitlines()
        return [Config(self.client_config, id_, is_immutable_id=True) for id_ in ids]

    def remove(self, x: Union[ValidConfig, List[ValidConfig]]):
        """Remove one or more configs.

        # Arguments
            x: One or a list of configs. Valid values are the id of the config or
                a `python_on_whales.Config` object.
        """
        full_cmd = self.docker_cmd + ["config", "rm"]
        full_cmd += to_list(x)
        run(full_cmd)
