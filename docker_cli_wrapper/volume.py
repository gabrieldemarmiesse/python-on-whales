import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import pydantic
from typeguard import typechecked

from .utils import ValidPath, run

VolumeDefinition = Union[Tuple[ValidPath, ValidPath, str], Tuple[ValidPath, ValidPath]]


class Volume:
    def __init__(self, docker_cmd: List[str], name: str):
        self._docker_cmd = docker_cmd
        self.name = name
        self._volume_inspect_result: Optional[VolumeInspectResult] = None
        self._last_refreshed_time = datetime.min

    def _needs_reload(self) -> bool:
        return (datetime.now() - self._last_refreshed_time) <= 0.2

    def reload(self):
        json_str = run(self._docker_cmd + ["volume", "inspect", self.name])
        json_obj = json.loads(json_str)[0]
        self._volume_inspect_result = VolumeInspectResult.parse_obj(json_obj)

    def _reload_if_necessary(self):
        if self._needs_reload():
            self.reload()

    @property
    def created_at(self) -> datetime:
        self._reload_if_necessary()
        return self._volume_inspect_result.CreatedAt

    @property
    def driver(self) -> str:
        self._reload_if_necessary()
        return self._volume_inspect_result.Driver


VolumeArg = Union[Volume, str]


class VolumeCLI:
    def __init__(self, docker_cmd: List[str]):
        self._docker_cmd = docker_cmd

    def _make_cli_cmd(self) -> List[str]:
        return self._docker_cmd + ["volume"]

    def create(self, volume_name: Optional[str] = None) -> Volume:
        full_cmd = self._make_cli_cmd() + ["create"]

        if volume_name is not None:
            full_cmd += [volume_name]

        return Volume(self._docker_cmd, run(full_cmd))

    @typechecked
    def remove(self, x: Union[VolumeArg, List[VolumeArg]]) -> List[str]:
        full_cmd = self._make_cli_cmd() + ["remove"]

        for v in to_list(x):
            full_cmd.append(_get_name(v))

        return run(full_cmd).split("\n")


def _get_name(x: Union[Volume, str]) -> str:
    if isinstance(x, str):
        return x
    else:
        return x.name


def to_list(x) -> list:
    if isinstance(x, list):
        return x
    else:
        return [x]


class VolumeInspectResult(pydantic.BaseModel):
    CreatedAt: datetime
    Driver: str
    Labels: Dict[str, str]
    Mountpoint: Path
    Name: str
    Options: Optional[str]
    Scope: str
