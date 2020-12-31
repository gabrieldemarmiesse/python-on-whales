from __future__ import annotations

from datetime import datetime
from pathlib import Path
from subprocess import PIPE, Popen
from typing import Any, Dict, Iterator, List, Optional, Union, overload

import pydantic

import python_on_whales.components.buildx
import python_on_whales.components.container
from python_on_whales.client_config import (
    ClientConfig,
    DockerCLICaller,
    ReloadableObjectFromJson,
)
from python_on_whales.utils import (
    DockerCamelModel,
    DockerException,
    ValidPath,
    format_dict_for_cli,
    run,
    stream_stdout_and_stderr,
    to_list,
)


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
    def create(self):
        """Not yet implemented"""
        raise NotImplementedError

    def inspect(self):
        """Not yet implemented"""
        raise NotImplementedError

    def list(self):
        """Not yet implemented"""
        raise NotImplementedError

    def remove(self, x: Union[ValidConfig, List[ValidConfig]]):
        """Remove one or more config.

        # Arguments
            x: One or a list of configs. Valid values are the id of the config or
                a `python_on_whales.Config` object.
        """
        full_cmd = self.docker_cmd + ["config", "rm"]
        full_cmd += to_list(x)
        run(full_cmd)
