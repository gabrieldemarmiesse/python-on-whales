import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import pydantic
from typeguard import typechecked

from docker_cli_wrapper.docker_command import DockerCommand
from docker_cli_wrapper.utils import ReloadableObject, ValidPath, run, to_list


class VolumeInspectResult(pydantic.BaseModel):
    CreatedAt: datetime
    Driver: str
    Labels: Dict[str, str]
    Mountpoint: Path
    Name: str
    Options: Optional[Dict[str, str]]
    Scope: str


class Volume(ReloadableObject):
    def __init__(self, docker_cmd: DockerCommand, name: str):
        self.docker_cmd = docker_cmd
        self.name = name
        self._volume_inspect_result: Optional[VolumeInspectResult] = None
        super().__init__()

    def __str__(self):
        return self.name

    def reload(self):
        json_str = run(self.docker_cmd.as_list() + ["volume", "inspect", self.name])
        json_obj = json.loads(json_str)[0]
        self._volume_inspect_result = VolumeInspectResult.parse_obj(json_obj)

    def __eq__(self, other):
        if not isinstance(other, Volume):
            raise TypeError(f"Cannot compare a docker volume with {type(other)}.")
        return self.name == other.name and self.docker_cmd == other.docker_cmd

    @property
    def created_at(self) -> datetime:
        self._reload_if_necessary()
        return self._volume_inspect_result.CreatedAt

    @property
    def driver(self) -> str:
        self._reload_if_necessary()
        return self._volume_inspect_result.Driver

    @property
    def labels(self) -> Dict[str, str]:
        self._reload_if_necessary()
        return self._volume_inspect_result.Labels


VolumeArg = Union[Volume, str]


class VolumeCLI:
    def __init__(self, docker_cmd: DockerCommand):
        self.docker_cmd = docker_cmd

    def create(
        self,
        volume_name: Optional[str] = None,
        driver: Optional[str] = None,
        labels: Dict[str, str] = {},
        options: Dict[str, str] = {},
    ) -> Volume:
        full_cmd = self.docker_cmd.as_list() + ["volume", "create"]

        if volume_name is not None:
            full_cmd += [volume_name]
        if driver is not None:
            full_cmd += ["--driver", driver]

        for key, value in labels.items():
            full_cmd += ["--label", f"{key}={value}"]

        for key, value in options.items():
            full_cmd += ["--opt", f"{key}={value}"]

        return Volume(self.docker_cmd, run(full_cmd))

    @typechecked
    def remove(self, x: Union[VolumeArg, List[VolumeArg]]) -> List[str]:
        full_cmd = self.docker_cmd.as_list() + ["volume", "remove"]

        for v in to_list(x):
            full_cmd.append(str(v))

        return run(full_cmd).split("\n")

    @typechecked
    def prune(self, filters: Dict[str, str] = {}, force: bool = False):
        full_cmd = self.docker_cmd.as_list() + ["volume", "prune"]

        for key, value in filters.items():
            full_cmd += ["--filter", f"{key}={value}"]

        if force:
            full_cmd.append("--force")

        return run(full_cmd, capture_stderr=False, capture_stdout=False)

    @typechecked
    def list(self, filters: Dict[str, str] = {}) -> List[Volume]:
        full_cmd = self.docker_cmd.as_list() + ["volume", "list", "--quiet"]

        for key, value in filters.items():
            full_cmd += ["--filter", f"{key}={value}"]

        volumes_names = run(full_cmd).splitlines()

        return [Volume(self.docker_cmd, name=x) for x in volumes_names]


VolumeDefinition = Union[
    Tuple[Union[Volume, ValidPath], ValidPath],
    Tuple[Union[Volume, ValidPath], ValidPath, str],
]
