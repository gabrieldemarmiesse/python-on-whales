from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import pydantic
from typeguard import typechecked

from .utils import ValidPath, run

VolumeDefinition = Union[Tuple[ValidPath, ValidPath, str], Tuple[ValidPath, ValidPath]]


class VolumeCLI:
    def __init__(self, docker_cmd: List[str]):
        self.docker_cmd = docker_cmd

    def _make_cli_cmd(self) -> List[str]:
        return self.docker_cmd + ["volume"]

    def create(self, volume_name: Optional[str] = None) -> str:
        full_cmd = self._make_cli_cmd() + ["create"]

        if volume_name is not None:
            full_cmd += [volume_name]

        return run(full_cmd)

    @typechecked
    def remove(self, x: Union[str, List[str]]) -> List[str]:
        full_cmd = self._make_cli_cmd() + ["remove"]
        if isinstance(x, str):
            full_cmd.append(x)
        if isinstance(x, list):
            full_cmd += x

        return run(full_cmd).split("\n")


class Volume:
    def __init__(self, volume_id):
        self.id = volume_id


class VolumeInspectResult(pydantic.BaseModel):
    CreatedAt: datetime
    Driver: str
    Labels: Dict[str, str]
    Mountpoint: Path
    Name: str
    Options: Optional[str]
    Scope: str
