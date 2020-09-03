import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import pydantic

from docker_cli_wrapper.client_config import (
    ClientConfig,
    DockerCLICaller,
    ReloadableObject,
)
from docker_cli_wrapper.utils import ValidPath, run, to_list


class VolumeInspectResult(pydantic.BaseModel):
    CreatedAt: datetime
    Driver: str
    Labels: Dict[str, str]
    Mountpoint: Path
    Name: str
    Options: Optional[Dict[str, str]]
    Scope: str


class Volume(ReloadableObject):
    def __init__(self, client_config: ClientConfig, name: str):

        self.name = name
        super().__init__(client_config)

    def __str__(self):
        return self.name

    def _reload(self):
        json_str = run(self.docker_cmd + ["volume", "inspect", self.name])
        json_obj = json.loads(json_str)[0]
        self._inspect_result = VolumeInspectResult.parse_obj(json_obj)

    def __eq__(self, other):
        if not isinstance(other, Volume):
            raise TypeError(f"Cannot compare a docker volume with {type(other)}.")
        return self.name == other.name and self.docker_cmd == other.docker_cmd

    @property
    def created_at(self) -> datetime:
        self._reload_if_necessary()
        return self.get_inspect_result().CreatedAt

    @property
    def driver(self) -> str:
        self._reload_if_necessary()
        return self.get_inspect_result().Driver

    @property
    def labels(self) -> Dict[str, str]:
        self._reload_if_necessary()
        return self.get_inspect_result().Labels


VolumeArg = Union[Volume, str]


class VolumeCLI(DockerCLICaller):
    def create(
        self,
        volume_name: Optional[str] = None,
        driver: Optional[str] = None,
        labels: Dict[str, str] = {},
        options: Dict[str, str] = {},
    ) -> Volume:
        full_cmd = self.docker_cmd + ["volume", "create"]

        if volume_name is not None:
            full_cmd += [volume_name]
        if driver is not None:
            full_cmd += ["--driver", driver]

        for key, value in labels.items():
            full_cmd += ["--label", f"{key}={value}"]

        for key, value in options.items():
            full_cmd += ["--opt", f"{key}={value}"]

        return Volume(self.client_config, run(full_cmd))

    def remove(self, x: Union[VolumeArg, List[VolumeArg]]) -> List[str]:
        full_cmd = self.docker_cmd + ["volume", "remove"]

        for v in to_list(x):
            full_cmd.append(str(v))

        return run(full_cmd).split("\n")

    def prune(self, filters: Dict[str, str] = {}, force: bool = False):
        full_cmd = self.docker_cmd + ["volume", "prune"]

        for key, value in filters.items():
            full_cmd += ["--filter", f"{key}={value}"]

        if force:
            full_cmd.append("--force")

        return run(full_cmd, capture_stderr=False, capture_stdout=False)

    def list(self, filters: Dict[str, str] = {}) -> List[Volume]:
        full_cmd = self.docker_cmd + ["volume", "list", "--quiet"]

        for key, value in filters.items():
            full_cmd += ["--filter", f"{key}={value}"]

        volumes_names = run(full_cmd).splitlines()

        return [Volume(self.client_config, name=x) for x in volumes_names]


VolumeDefinition = Union[
    Tuple[Union[Volume, ValidPath], ValidPath],
    Tuple[Union[Volume, ValidPath], ValidPath, str],
]
