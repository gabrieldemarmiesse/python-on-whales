import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import python_on_whales.components.buildx
import python_on_whales.components.container
from python_on_whales.client_config import (
    ClientConfig,
    DockerCLICaller,
    ReloadableObjectFromJson,
)
from python_on_whales.utils import DockerCamelModel, ValidPath, run, to_list


class VolumeInspectResult(DockerCamelModel):
    created_at: datetime
    driver: str
    labels: Dict[str, str]
    mountpoint: Path
    name: str
    options: Optional[Dict[str, str]]
    scope: str


class Volume(ReloadableObjectFromJson):
    def __init__(
        self, client_config: ClientConfig, reference: str, is_immutable_id=False
    ):
        super().__init__(client_config, "name", reference, is_immutable_id)

    def _fetch_inspect_result_json(self, reference):
        return run(self.docker_cmd + ["volume", "inspect", reference])

    def _parse_json_object(self, json_object: Dict[str, Any]):
        return VolumeInspectResult.parse_obj(json_object)

    @property
    def name(self) -> str:
        return self._get_immutable_id()

    @property
    def created_at(self) -> datetime:
        return self._get_inspect_result().created_at

    @property
    def driver(self) -> str:
        return self._get_inspect_result().driver

    @property
    def labels(self) -> Dict[str, str]:
        return self._get_inspect_result().labels


ValidVolume = Union[Volume, str]
VolumePath = Tuple[Union[Volume, str], ValidPath]


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

    def remove(self, x: Union[ValidVolume, List[ValidVolume]]):
        """Removes one or more volumes

        # Arguments:
            x: A volume or a list of volumes.
        """

        full_cmd = self.docker_cmd + ["volume", "remove"]

        for v in to_list(x):
            full_cmd.append(str(v))

        run(full_cmd)

    def cp(
        self,
        source: Union[ValidPath, VolumePath],
        destination: Union[ValidPath, VolumePath],
    ):
        """Copy files/folders between a volume and the local filesystem."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = Path(temp_dir)
            content = "FROM scratch\nCOPY Dockerfile /\nCMD /Dockerfile"
            (temp_dir / "Dockerfile").write_text(content)
            buildx = python_on_whales.components.buildx.BuildxCLI(self.client_config)
            dummy_image = buildx.build(temp_dir, tags="python-on-whales-temp-image")

        container = python_on_whales.components.container.ContainerCLI(
            self.client_config
        )
        volume_name = str(source[0])
        volume_in_container = Path("/volume")
        dummy_container = container.create(
            dummy_image, volumes=[(volume_name, volume_in_container)]
        )
        container.cp((dummy_container, volume_in_container / source[1]), destination)
        dummy_container.remove()
        dummy_image.remove()

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
