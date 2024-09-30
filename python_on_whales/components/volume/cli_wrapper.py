from __future__ import annotations

import json
import os
import tempfile
import warnings
from datetime import datetime
from pathlib import Path
from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Literal,
    Mapping,
    Optional,
    Tuple,
    Union,
    overload,
)

from typing_extensions import TypeAlias

import python_on_whales.components.buildx
import python_on_whales.components.container
import python_on_whales.components.image
from python_on_whales.client_config import (
    ClientConfig,
    DockerCLICaller,
    ReloadableObjectFromJson,
)
from python_on_whales.components.volume.models import VolumeInspectResult
from python_on_whales.exceptions import NoSuchVolume
from python_on_whales.test_utils import random_name
from python_on_whales.utils import ValidPath, run, to_list

VolumeListFilter: TypeAlias = Union[
    Tuple[Literal["driver"], str],
    Tuple[Literal["opt"], str],
    Tuple[Literal["label"], str],
    Tuple[Literal["label!"], str],
    Tuple[Literal["name"], str],
    Tuple[Literal["scope"], Literal["swarm", "global", "local"]],
    Tuple[Literal["after", "since"], str],
    Tuple[Literal["until"], str],  # TODO: allow datetime
    Tuple[Literal["dangling"], str],  # TODO: allow bool
]


class Volume(ReloadableObjectFromJson):
    def __init__(
        self, client_config: ClientConfig, reference: str, is_immutable_id=False
    ):
        super().__init__(client_config, "name", reference, is_immutable_id)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.remove()

    def _fetch_inspect_result_json(self, reference):
        json_str = run(self.docker_cmd + ["volume", "inspect", reference])
        return json.loads(json_str)[0]

    def _parse_json_object(self, json_object: Dict[str, Any]):
        return VolumeInspectResult(**json_object)

    def _get_inspect_result(self) -> VolumeInspectResult:
        """Only there to allow tools to know the return type"""
        return super()._get_inspect_result()

    @property
    def name(self) -> str:
        return self._get_immutable_id()

    @property
    def driver(self) -> str:
        return self._get_inspect_result().driver

    @property
    def mountpoint(self) -> Path:
        return self._get_inspect_result().mountpoint

    @property
    def created_at(self) -> datetime:
        return self._get_inspect_result().created_at

    @property
    def status(self) -> Optional[Dict[str, Any]]:
        return self._get_inspect_result().status

    @property
    def labels(self) -> Dict[str, str]:
        return self._get_inspect_result().labels

    @property
    def scope(self) -> str:
        return self._get_inspect_result().scope

    @property
    def options(self) -> Optional[Dict[str, str]]:
        return self._get_inspect_result().options

    def __repr__(self):
        return f"python_on_whales.Volume(name='{self.name}', driver={self.driver})"

    def remove(self) -> None:
        """Removes this volume"""
        VolumeCLI(self.client_config).remove(self)

    def clone(
        self,
        new_volume_name: Optional[str] = None,
        driver: Optional[str] = None,
        labels: Dict[str, str] = {},
        options: Dict[str, str] = {},
    ) -> "Volume":
        """Creates a new volume and copy all the data inside.

        See the [`docker.volume.clone`](../sub-commands/volume.md#clone) command for
        information about the arguments.
        """
        return VolumeCLI(self.client_config).clone(
            self, new_volume_name, driver, labels, options
        )

    def exists(self) -> bool:
        """Returns `True` if the docker volume exists and `False` if it doesn't exists.

        If it doesn't exists, it most likely mean that it was removed.

         See the `docker.volume.exists` command for information about the arguments.
        """
        return VolumeCLI(self.client_config).exists(self.name)


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

        Parameters:
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

    @overload
    def inspect(self, x: str) -> Volume: ...

    @overload
    def inspect(self, x: List[str]) -> List[Volume]: ...

    def inspect(self, x: Union[str, List[str]]) -> Union[Volume, List[Volume]]:
        if isinstance(x, str):
            return Volume(self.client_config, x)
        else:
            return [Volume(self.client_config, reference) for reference in x]

    def exists(self, x: str) -> bool:
        """Returns `True` if the volume exists. `False` otherwise.

         It's just calling `docker.volume.inspect(...)` and verifies that it doesn't throw
         a `python_on_whales.exceptions.NoSuchVolume`.

        # Returns
            A `bool`
        """
        try:
            self.inspect(x)
        except NoSuchVolume:
            return False
        else:
            return True

    def list(
        self, filters: Union[Iterable[VolumeListFilter], Mapping[str, Any]] = ()
    ) -> List[Volume]:
        """List volumes

        Parameters:
            filters: See the [Docker documentation page about filtering
                ](https://docs.docker.com/engine/reference/commandline/volume_ls/#filtering).
                An example `filters=[("dangling", "true"), ("driver", "local")]`.

        # Returns
            `List[python_on_whales.Volume]`
        """
        if isinstance(filters, Mapping):
            filters = filters.items()
            warnings.warn(
                "Passing filters as a mapping is deprecated, replace with an "
                "iterable of tuples instead, as so:\n"
                f"filters={list(filters)}",
                DeprecationWarning,
            )
        full_cmd = self.docker_cmd + ["volume", "list", "--quiet"]
        full_cmd.add_args_iterable("--filter", (f"{f[0]}={f[1]}" for f in filters))

        volumes_names = run(full_cmd).splitlines()

        return [
            Volume(self.client_config, x, is_immutable_id=True) for x in volumes_names
        ]

    def prune(
        self,
        filters: Union[Iterable[VolumeListFilter], Mapping[str, Any]] = (),
        all: bool = False,
    ) -> None:
        """Remove volumes

        Parameters:
            filters: See the [Docker documentation page about filtering
                ](https://docs.docker.com/engine/reference/commandline/volume_ls/#filtering).
                An example `filters=[("dangling", "true"), ("driver", "local")]`.
            all: Remove all unused volumes, not just anonymous ones.
        """
        if isinstance(filters, Mapping):
            filters = filters.items()
            warnings.warn(
                "Passing filters as a mapping is deprecated, replace with an "
                "iterable of tuples instead, as so:\n"
                f"filters={list(filters)}",
                DeprecationWarning,
            )
        full_cmd = self.docker_cmd + ["volume", "prune", "--force"]
        full_cmd.add_flag("--all", all)
        full_cmd.add_args_iterable("--filter", (f"{f[0]}={f[1]}" for f in filters))

        run(full_cmd)

    def remove(self, x: Union[ValidVolume, List[ValidVolume]]):
        """Removes one or more volumes

        Parameters:
            x: A volume or a list of volumes. An empty list as argument means
                nothing is done.
        """

        full_cmd = self.docker_cmd + ["volume", "remove"]
        if x == []:
            return
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

        Parameters:
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
            self.copy((source, "."), temp_dir)
            self.copy(str(temp_dir) + "/.", (new_volume, ""))
        return new_volume

    def copy(
        self,
        source: Union[ValidPath, VolumePath],
        destination: Union[ValidPath, VolumePath],
    ):
        """Copy files/folders between a volume and the local filesystem.

        Parameters:
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
            buildx = python_on_whales.components.buildx.cli_wrapper.BuildxCLI(
                self.client_config
            )
            image_name = random_name()
            dummy_image = buildx.build(
                temp_dir, tags=image_name, progress=False, load=True
            )

        container = python_on_whales.components.container.cli_wrapper.ContainerCLI(
            self.client_config
        )
        volume_in_container = Path("/volume")
        if isinstance(source, tuple):
            volume_name = str(source[0])

            dummy_container = container.create(
                dummy_image, volumes=[(volume_name, volume_in_container)]
            )
            container.copy(
                (dummy_container, os.path.join(volume_in_container, source[1])),
                destination,
            )
        elif isinstance(destination, tuple):
            volume_name = str(destination[0])
            dummy_container = container.create(
                dummy_image, volumes=[(volume_name, volume_in_container)]
            )
            container.copy(
                source,
                (dummy_container, os.path.join(volume_in_container, destination[1])),
            )
        else:
            raise ValueError("source or destination should be a tuple.")
        dummy_container.remove()
        python_on_whales.components.image.cli_wrapper.ImageCLI(
            self.client_config
        ).remove(image_name)


VolumeDefinition = Union[
    Tuple[Union[Volume, ValidPath], ValidPath],
    Tuple[Union[Volume, ValidPath], ValidPath, str],
]
