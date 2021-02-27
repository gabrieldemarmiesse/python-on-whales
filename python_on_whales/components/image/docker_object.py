from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Iterator, List, Optional, Union

import python_on_whales.components.container
import python_on_whales.components.image.cli_wrapper
from python_on_whales.client_config import ClientConfig, ReloadableObjectFromJson
from python_on_whales.components.image.models import (
    ImageGraphDriver,
    ImageInspectResult,
    ImageRootFS,
)
from python_on_whales.utils import ValidPath, run


class Image(ReloadableObjectFromJson):
    def __init__(
        self, client_config: ClientConfig, reference: str, is_immutable_id=False
    ):
        super().__init__(client_config, "id", reference, is_immutable_id)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.remove(force=True)

    def _fetch_inspect_result_json(self, reference):
        return run(self.docker_cmd + ["image", "inspect", reference])

    def _parse_json_object(self, json_object: Dict[str, Any]) -> ImageInspectResult:
        return ImageInspectResult.parse_obj(json_object)

    def _get_inspect_result(self) -> ImageInspectResult:
        """Only there to allow tools to know the return type"""
        return super()._get_inspect_result()

    @property
    def id(self) -> str:
        return self._get_immutable_id()

    @property
    def repo_tags(self) -> List[str]:
        return self._get_inspect_result().repo_tags

    @property
    def repo_digests(self) -> List[str]:
        return self._get_inspect_result().repo_digests

    @property
    def parent(self) -> str:
        return self._get_inspect_result().parent

    @property
    def comment(self) -> str:
        return self._get_inspect_result().comment

    @property
    def created(self) -> datetime:
        return self._get_inspect_result().created

    @property
    def container(self) -> str:
        return self._get_inspect_result().container

    @property
    def container_config(self) -> python_on_whales.components.container.ContainerConfig:
        return self._get_inspect_result().container_config

    @property
    def docker_version(self) -> str:
        return self._get_inspect_result().docker_version

    @property
    def author(self) -> str:
        return self._get_inspect_result().author

    @property
    def config(self) -> python_on_whales.components.container.ContainerConfig:
        return self._get_inspect_result().config

    @property
    def architecture(self) -> str:
        return self._get_inspect_result().architecture

    @property
    def os(self) -> str:
        return self._get_inspect_result().os

    @property
    def os_version(self) -> str:
        return self._get_inspect_result().os_version

    @property
    def size(self) -> int:
        return self._get_inspect_result().size

    @property
    def virtual_size(self) -> int:
        return self._get_inspect_result().virtual_size

    @property
    def graph_driver(self) -> ImageGraphDriver:
        return self._get_inspect_result().graph_driver

    @property
    def root_fs(self) -> ImageRootFS:
        return self._get_inspect_result().root_fs

    @property
    def metadata(self) -> Optional[Dict[str, str]]:
        return self._get_inspect_result().metadata

    def remove(self, force: bool = False, prune: bool = True):
        """Remove this Docker image.

        See the [`docker.image.remove`](../sub-commands/container.md#remove) command for
        information about the arguments.
        """
        python_on_whales.components.image.cli_wrapper.ImageCLI(
            self.client_config
        ).remove(self, force, prune)

    def save(self, output: Optional[ValidPath] = None) -> Optional[Iterator[bytes]]:
        """Saves this Docker image in a tar.

        See the [`docker.image.save`](../sub-commands/container.md#save) command for
        information about the arguments.
        """
        return python_on_whales.components.image.cli_wrapper.ImageCLI(
            self.client_config
        ).save(self, output)

    def tag(self, new_tag: str) -> None:
        """Add a tag to a Docker image.

        See the [`docker.image.tag`](../sub-commands/container.md#tag) command for
        information about the arguments.
        """
        return python_on_whales.components.image.cli_wrapper.ImageCLI(
            self.client_config
        ).tag(self, new_tag)

    def copy_from(self, path_in_image: ValidPath, destination: ValidPath):
        """Copy a file from a docker image in the local filesystem.

        See the `docker.image.copy_from` command for information about the arguments.
        """
        return python_on_whales.components.image.cli_wrapper.ImageCLI(
            self.client_config
        ).copy_from(self, path_in_image, destination)

    def copy_to(
        self,
        local_path: ValidPath,
        path_in_image: ValidPath,
        new_tag: Optional[str] = None,
    ) -> python_on_whales.components.image.cli_wrapper.Image:
        """Copy a file from the local filesystem in a docker image to create a new
        docker image.

        As if you did a dockerfile with a COPY instruction.

        See the `docker.image.copy_to` command for information about the arguments.
        """
        return python_on_whales.components.image.cli_wrapper.ImageCLI(
            self.client_config
        ).copy_to(self, local_path, path_in_image, new_tag)


ValidImage = Union[str, Image]
