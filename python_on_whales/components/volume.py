import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pydantic

from python_on_whales.client_config import (
    ClientConfig,
    DockerCLICaller,
    ReloadableObjectFromJson,
)
from python_on_whales.utils import ValidPath, run, to_list


class VolumeInspectResult(pydantic.BaseModel):
    CreatedAt: datetime
    Driver: str
    Labels: Dict[str, str]
    Mountpoint: Path
    Name: str
    Options: Optional[Dict[str, str]]
    Scope: str


class Volume(ReloadableObjectFromJson):
    def __init__(
        self, client_config: ClientConfig, reference: str, is_immutable_id=False
    ):
        super().__init__(client_config, "Name", reference, is_immutable_id)

    def _fetch_inspect_result_json(self, reference):
        return run(self.docker_cmd + ["volume", "inspect", reference])

    def _parse_json_object(self, json_object: Dict[str, Any]):
        return VolumeInspectResult.parse_obj(json_object)

    @property
    def name(self) -> str:
        return self._get_immutable_id()

    @property
    def created_at(self) -> datetime:
        return self._get_inspect_result().CreatedAt

    @property
    def driver(self) -> str:
        return self._get_inspect_result().Driver

    @property
    def labels(self) -> Dict[str, str]:
        return self._get_inspect_result().Labels


ValidVolume = Union[Volume, str]


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

    def remove(self, x: Union[ValidVolume, List[ValidVolume]]) -> List[str]:
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

        return [
            Volume(self.client_config, x, is_immutable_id=True) for x in volumes_names
        ]


VolumeDefinition = Union[
    Tuple[Union[Volume, ValidPath], ValidPath],
    Tuple[Union[Volume, ValidPath], ValidPath, str],
]
