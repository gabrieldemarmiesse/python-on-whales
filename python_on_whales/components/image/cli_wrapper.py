from __future__ import annotations

from datetime import datetime
from pathlib import Path
from subprocess import PIPE, Popen
from typing import Any, Dict, Iterator, List, Optional, Union, overload

import python_on_whales.components.buildx.cli_wrapper
import python_on_whales.components.container.cli_wrapper
from python_on_whales.client_config import (
    ClientConfig,
    DockerCLICaller,
    ReloadableObjectFromJson,
)
from python_on_whales.components.image.models import (
    ImageGraphDriver,
    ImageInspectResult,
    ImageRootFS,
)
from python_on_whales.utils import (
    DockerException,
    ValidPath,
    format_dict_for_cli,
    run,
    stream_stdout_and_stderr,
    to_list,
)


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
    def container_config(
        self,
    ) -> python_on_whales.components.container.cli_wrapper.ContainerConfig:
        return self._get_inspect_result().container_config

    @property
    def docker_version(self) -> str:
        return self._get_inspect_result().docker_version

    @property
    def author(self) -> str:
        return self._get_inspect_result().author

    @property
    def config(
        self,
    ) -> python_on_whales.components.container.cli_wrapper.ContainerConfig:
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
        ImageCLI(self.client_config).remove(self, force, prune)

    def save(self, output: Optional[ValidPath] = None) -> Optional[Iterator[bytes]]:
        """Saves this Docker image in a tar.

        See the [`docker.image.save`](../sub-commands/container.md#save) command for
        information about the arguments.
        """
        return ImageCLI(self.client_config).save(self, output)

    def tag(self, new_tag: str) -> None:
        """Add a tag to a Docker image.

        See the [`docker.image.tag`](../sub-commands/container.md#tag) command for
        information about the arguments.
        """
        return ImageCLI(self.client_config).tag(self, new_tag)

    def copy_from(self, path_in_image: ValidPath, destination: ValidPath):
        """Copy a file from a docker image in the local filesystem.

        See the `docker.image.copy_from` command for information about the arguments.
        """
        return ImageCLI(self.client_config).copy_from(self, path_in_image, destination)

    def copy_to(
        self,
        local_path: ValidPath,
        path_in_image: ValidPath,
        new_tag: Optional[str] = None,
    ) -> Image:
        """Copy a file from the local filesystem in a docker image to create a new
        docker image.

        As if you did a dockerfile with a COPY instruction.

        See the `docker.image.copy_to` command for information about the arguments.
        """
        return ImageCLI(self.client_config).copy_to(
            self, local_path, path_in_image, new_tag
        )


ValidImage = Union[str, Image]


class ImageCLI(DockerCLICaller):
    def __init__(self, client_config: ClientConfig):
        super().__init__(client_config)
        self.build = python_on_whales.components.buildx.cli_wrapper.BuildxCLI(
            client_config
        ).build

    def history(self):
        """Not yet implemented"""
        raise NotImplementedError

    def import_(
        self,
        source: ValidPath,
        tag: Optional[str] = None,
        changes: List[str] = [],
        message: Optional[str] = None,
        platform: Optional[str] = None,
    ) -> Image:
        """Import the contents from a tarball to create a filesystem image

        Alias: `docker.import_(...)`

        # Arguments
            changes: Apply Dockerfile instruction to the created image
            message: Set commit message for imported image
            platform: Set platform if server is multi-platform capable
        """
        full_cmd = self.docker_cmd + ["image", "import"]
        full_cmd.add_args_list("--change", changes)
        full_cmd.add_simple_arg("--message", message)
        full_cmd.add_simple_arg("--platform", platform)
        full_cmd.append(source)
        if tag is not None:
            full_cmd.append(tag)
        return Image(self.client_config, run(full_cmd))

    @overload
    def inspect(self, x: str) -> Image:
        ...

    @overload
    def inspect(self, x: List[str]) -> List[Image]:
        ...

    def inspect(self, x: Union[str, List[str]]) -> Union[Image, List[Image]]:
        """Creates a `python_on_whales.Image` object."""
        if isinstance(x, list):
            return [Image(self.client_config, identifier) for identifier in x]
        else:
            return Image(self.client_config, x)

    def load(
        self, input: Union[ValidPath, bytes, Iterator[bytes]], quiet: bool = False
    ) -> List[str]:
        """Loads one or multiple Docker image(s) from a tar or an iterator of `bytes`.

        Alias: `docker.load(...)`

        # Arguments
            input: Path or input stream to load the images from.
            quiet: If you don't want to display the progress bars.

        # Returns
            `None` when using bytes as input. A `List[str]` (list of tags)
             when a path is provided.
        """
        full_cmd = self.docker_cmd + ["image", "load"]

        if isinstance(input, (str, Path)):
            full_cmd += ["--input", str(input)]

        if quiet:
            full_cmd.append("--quiet")

        if isinstance(input, (str, Path)):
            all_tags = []
            for source, stream_bytes in stream_stdout_and_stderr(full_cmd):
                decoded = stream_bytes.decode()[:-1]
                if not quiet:
                    print(decoded)
                if "Loaded image" in decoded:
                    all_tags.append(decoded.split(" ")[-1])
            return all_tags

        if isinstance(input, bytes):
            input = [input]

        stdout_lines = self._load_from_generator(full_cmd, input)
        all_tags = []
        for line in stdout_lines:
            if "Loaded image" in line:
                all_tags.append(line.split(" ")[-1])
        return all_tags

    def _load_from_generator(self, full_cmd: List[str], input: Iterator[bytes]):
        p = Popen(full_cmd, stdin=PIPE, stdout=PIPE)
        for buffer_bytes in input:
            p.stdin.write(buffer_bytes)
            p.stdin.flush()
        p.stdin.close()
        stdout = p.stdout.read()
        p.stdout.close()
        exit_code = p.wait()
        if exit_code != 0:
            raise DockerException(full_cmd, exit_code)
        return stdout.decode().splitlines()

    def list(self) -> List[Image]:
        """Returns the list of Docker images present on the machine.

        Alias: `docker.images()`

        Note that each image may have multiple tags.

        # Returns
            A `List[python_on_whales.Image]` object.
        """
        full_cmd = self.docker_cmd + [
            "image",
            "list",
            "--quiet",
            "--no-trunc",
        ]

        ids = run(full_cmd).splitlines()
        # the list of tags is bigger than the number of images. We uniquify
        ids = set(ids)

        return [Image(self.client_config, x, is_immutable_id=True) for x in ids]

    def prune(self, all: bool = False, filter: Dict[str, str] = {}) -> None:
        """Remove unused images

        # Arguments
            all: Remove all unused images, not just dangling ones
            filter: Provide filter values (e.g. `{"until": "<timestamp>"}`)
        """
        full_cmd = self.docker_cmd + ["image", "prune"]
        full_cmd.add_flag("--all", all)
        full_cmd.add_args_list("--filter", format_dict_for_cli(filter))
        run(full_cmd)

    def pull(self, image_name: str, quiet: bool = False) -> Image:
        """Pull a docker image

        Alias: `docker.pull(...)`

        # Arguments
            image_name: The image name
            quiet: If you don't want to see the progress bars.

        # Returns:
            The Docker image loaded (`python_on_whales.Image` object).
        """
        full_cmd = self.docker_cmd + ["image", "pull"]

        if quiet:
            full_cmd.append("--quiet")

        full_cmd.append(image_name)
        run(full_cmd, capture_stdout=quiet, capture_stderr=quiet)
        return Image(self.client_config, image_name)

    def push(self, tag_or_repo: str, quiet: bool = False):
        """Push a tag or a repository to a registry

        Alias: `docker.push(...)`

        # Arguments
            tag_or_repo: Tag or repo to push
            quiet: If you don't want to see the progress bars.
        """
        full_cmd = self.docker_cmd + ["image", "push"]

        full_cmd.append(tag_or_repo)
        run(full_cmd, capture_stdout=quiet, capture_stderr=quiet)

    def remove(
        self,
        x: Union[ValidImage, List[ValidImage]],
        force: bool = False,
        prune: bool = True,
    ):
        """Remove one or more docker images.

        # Arguments
            x: Single image or list of Docker images to remove. You can use tags or
                `python_on_whales.Image` objects.
            force: Force removal of the image
            prune: Delete untagged parents
        """

        full_cmd = self.docker_cmd + ["image", "remove"]
        full_cmd.add_flag("--force", force)
        full_cmd.add_flag("--no-prune", not prune)
        for image in to_list(x):
            full_cmd.append(image)

        run(full_cmd)

    def save(
        self,
        images: Union[ValidImage, List[ValidImage]],
        output: Optional[ValidPath] = None,
    ) -> Optional[Iterator[bytes]]:
        """Save one or more images to a tar archive. Returns a stream if output is `None`

        Alias: `docker.save(...)`

        # Arguments
            images: Single docker image or list of docker images to save
            output: Path of the tar archive to produce. If `output` is None, a generator
                of bytes is produced. It can be used to stream those bytes elsewhere,
                to another Docker daemon for example.

        # Returns
            `Optional[Iterator[bytes]]`. If output is a path, nothing is returned.

        An example of transfer of an image from a local Docker daemon to a remote Docker
        daemon. We assume that the remote machine has an ssh access:

        ```python
        from python_on_whales import DockerClient

        local_docker = DockerClient()
        remote_docker = DockerClient(host="ssh://my_user@186.167.32.84")

        image_name = "busybox:1"
        local_docker.pull(image_name)
        bytes_iterator = local_docker.image.save(image_name)

        remote_docker.image.load(bytes_iterator)
        ```

        Of course the best solution is to use a registry to transfer image but
        it's a cool example nonetheless.
        """
        full_cmd = self.docker_cmd + ["image", "save"]

        if output is not None:
            full_cmd += ["--output", str(output)]

        for image in to_list(images):
            full_cmd.append(str(image))
        if output is None:
            # we stream the bytes
            return self._save_generator(full_cmd)
        else:
            run(full_cmd)

    def _save_generator(self, full_cmd) -> Iterator[bytes]:
        full_cmd = [str(x) for x in full_cmd]
        p = Popen(full_cmd, stdout=PIPE, stderr=PIPE)
        for line in p.stdout:
            yield line
        exit_code = p.wait(0.1)
        if exit_code != 0:
            raise DockerException(full_cmd, exit_code, stderr=p.stderr.read())

    def tag(self, source_image: Union[Image, str], new_tag: str):
        """Adds a tag to a Docker image.

        Alias: `docker.tag(...)`

        # Arguments
            source_image: The Docker image to tag. You can use a tag to reference it.
            new_tag: The tag to add to the Docker image.
        """
        full_cmd = self.docker_cmd + [
            "image",
            "tag",
            str(source_image),
            new_tag,
        ]
        run(full_cmd)

    def _pull_if_necessary(self, image: ValidImage) -> Image:
        if isinstance(image, Image):
            # A docker image object must exist in the daemon to be defined.
            return image
        try:
            return self.inspect(image)
        except DockerException:
            print(f"Unable to find image '{image}' locally")
            return self.pull(image)

    def copy_from(
        self, image: ValidImage, path_in_image: ValidPath, destination: ValidPath
    ):
        with python_on_whales.components.container.cli_wrapper.ContainerCLI(
            self.client_config
        ).create(image) as tmp_container:
            tmp_container.copy_from(path_in_image, destination)

    def copy_to(
        self,
        base_image: ValidImage,
        local_path: ValidPath,
        path_in_image: ValidPath,
        new_tag: Optional[str] = None,
    ) -> Image:
        with python_on_whales.components.container.cli_wrapper.ContainerCLI(
            self.client_config
        ).create(base_image) as tmp_container:
            tmp_container.copy_to(local_path, path_in_image)
            return tmp_container.commit(tag=new_tag)
