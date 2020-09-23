import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import python_on_whales.components.buildx
import python_on_whales.components.container
import python_on_whales.components.image
from python_on_whales.client_config import (
    ClientConfig,
    DockerCLICaller,
    ReloadableObjectFromJson,
)
from python_on_whales.test_utils import random_name
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
        """Creates a volume

        # Arguments
            volume_name: The volume name, if not provided, a long random
                string will be used instead.
            driver: Specify volume driver name (default "local")
            labels: Set metadata for a volume
            options: Set driver specific options
        """
        full_cmd = self.docker_cmd + ["volume", "create"]

        full_cmd.add_simple_arg("--driver", driver)
        for key, value in labels.items():
            full_cmd += ["--label", f"{key}={value}"]
        for key, value in options.items():
            full_cmd += ["--opt", f"{key}={value}"]

        if volume_name is not None:
            full_cmd.append(volume_name)

        return Volume(self.client_config, run(full_cmd))

    def remove(self, x: Union[ValidVolume, List[ValidVolume]]):
        """Removes one or more volumes

        # Arguments
            x: A volume or a list of volumes.
        """

        full_cmd = self.docker_cmd + ["volume", "remove"]

        for v in to_list(x):
            full_cmd.append(str(v))

        run(full_cmd)

    def clone(
        self,
        source: ValidVolume,
        new_volume_name: Optional[str] = None,
        driver: Optional[str] = None,
        labels: Dict[str, str] = {},
        options: Dict[str, str] = {},
    ) -> Volume:
        """Clone a volume.

        # Arguments
            source: The volume to clone
            new_volume_name: The new volume name. If not given, a random name is chosen.
            driver: Specify volume driver name (default "local")
            labels: Set metadata for a volume
            options: Set driver specific options

        # Returns
            A `python_on_whales.Volume`, the new volume.
        """
        new_volume = self.create(new_volume_name, driver, labels, options)
        with tempfile.TemporaryDirectory() as temp_dir:
            self.cp((source, "."), temp_dir)
            self.cp(str(temp_dir) + "/.", (new_volume, ""))
        return new_volume

    def cp(
        self,
        source: Union[ValidPath, VolumePath],
        destination: Union[ValidPath, VolumePath],
    ):
        """Copy files/folders between a volume and the local filesystem.

        # Arguments
            source: If `source` is a directory/file inside a Docker volume,
                a tuple `(my_volume, path_in_volume)` must be provided. The volume
                can be a `python_on_whales.Volume` or a volume name as `str`. The path
                can be a `pathlib.Path` or a `str`. If `source` is  a local directory,
                a `pathlib.Path` or `str` should be provided. End the source path with
                `/.` if you want to copy the directory content in another directory.
            destination: Same as `source`.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = Path(temp_dir)
            content = "FROM scratch\nCOPY Dockerfile /\nCMD /Dockerfile"
            (temp_dir / "Dockerfile").write_text(content)
            buildx = python_on_whales.components.buildx.BuildxCLI(self.client_config)
            image_name = random_name()
            dummy_image = buildx.build(temp_dir, tags=image_name, progress=False)

        container = python_on_whales.components.container.ContainerCLI(
            self.client_config
        )
        volume_in_container = Path("/volume")
        if isinstance(source, tuple):
            volume_name = str(source[0])

            dummy_container = container.create(
                dummy_image, volumes=[(volume_name, volume_in_container)]
            )
            container.cp(
                (dummy_container, os.path.join(volume_in_container, source[1])),
                destination,
            )
        elif isinstance(destination, tuple):
            volume_name = str(destination[0])
            dummy_container = container.create(
                dummy_image, volumes=[(volume_name, volume_in_container)]
            )
            container.cp(
                source,
                (dummy_container, os.path.join(volume_in_container, destination[1])),
            )
        else:
            raise ValueError("source or destination should be a tuple.")
        dummy_container.rm()
        python_on_whales.components.image.ImageCLI(self.client_config).remove(
            image_name
        )

    def prune(self, filters: Dict[str, Union[str, int]] = {}) -> None:
        """Remove volumes

        # Arguments
            filters: See the [Docker documentation page about filtering
                ](https://docs.docker.com/engine/reference/commandline/volume_ls/#filtering).
                An example `filters=dict(dangling=1, driver="local")`.
        """
        full_cmd = self.docker_cmd + ["volume", "prune", "--force"]

        for key, value in filters.items():
            full_cmd += ["--filter", f"{key}={value}"]

        run(full_cmd, capture_stderr=False, capture_stdout=False)

    def list(self, filters: Dict[str, Union[str, int]] = {}) -> List[Volume]:
        """List volumes

        # Arguments
            filters: See the [Docker documentation page about filtering
                ](https://docs.docker.com/engine/reference/commandline/volume_ls/#filtering).
                An example `filters=dict(dangling=1, driver="local")`.

        # Returns
            `List[python_on_whales.Volume]`
        """

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
