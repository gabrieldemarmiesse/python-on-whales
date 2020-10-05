from __future__ import annotations

import inspect
from datetime import datetime
from pathlib import Path
from subprocess import PIPE, Popen
from typing import Any, Dict, Iterator, List, Optional, Union, overload

import python_on_whales.components.buildx
from python_on_whales.client_config import (
    ClientConfig,
    DockerCLICaller,
    ReloadableObjectFromJson,
)
from python_on_whales.utils import (
    DockerCamelModel,
    DockerException,
    ValidPath,
    run,
    to_list,
)


class ContainerConfigClass(DockerCamelModel):
    hostname: str
    domainname: str
    user: str
    attach_stdin: bool
    attach_stdout: bool
    attach_stderr: bool
    tty: bool
    open_stdin: bool
    stdin_once: bool
    env: Optional[List[str]]
    cmd: Optional[List[str]]
    image: str
    volume: Optional[List[str]]
    working_dir: Path
    entrypoint: Optional[List[str]]
    on_build: Optional[List[str]]
    labels: Optional[Dict[str, str]]


class ImageConfigClass(DockerCamelModel):
    hostname: str
    domainname: str
    user: str
    attach_stdin: bool
    attach_stdout: bool
    attach_stderr: bool
    tty: bool
    open_stdin: bool
    stdin_once: bool
    env: Optional[List[str]]
    cmd: Optional[List[str]]
    image: str
    volume: Optional[List[str]]
    working_dir: Path
    entrypoint: Optional[List[str]]
    on_build: Optional[List[str]]
    labels: Optional[Dict[str, str]]


class ImageInspectResult(DockerCamelModel):
    id: str
    repo_tags: List[str]
    repo_digests: List[str]
    parent: str
    comment: str
    created: datetime
    container: str
    container_config: ContainerConfigClass
    docker_version: str
    author: str
    architecture: str
    os: str
    size: int
    virtual_size: int
    graph_driver: Dict[str, Any]
    root_FS: Dict[str, Any]
    metadata: Dict[str, str]


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

    @property
    def id(self) -> str:
        return self._get_immutable_id()

    @property
    def repo_tags(self) -> List[str]:
        return self._get_inspect_result().repo_tags

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


ValidImage = Union[str, Image]


class ImageCLI(DockerCLICaller):
    def __init__(self, client_config: ClientConfig):
        super().__init__(client_config)
        self.build = python_on_whales.components.buildx.BuildxCLI(client_config).build

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
    ):
        """Loads one or multiple Docker image(s) from a tar or an iterator of `bytes`.

        # Arguments
            input: Path or input stream to load the images from.
            quiet: If you don't want to display the progress bars.

        # Returns
            `None` at the moment, but should return the Docker images loaded (not
            implemented yet).
        """
        full_cmd = self.docker_cmd + ["image", "load"]

        if isinstance(input, (str, Path)):
            full_cmd += ["--input", str(input)]

        if quiet:
            full_cmd.append("--quiet")

        if isinstance(input, (str, Path)):
            run(full_cmd)
        elif isinstance(input, bytes):
            run(full_cmd, input=input)
        elif inspect.isgenerator(input):
            self._load_from_generator(full_cmd, input)
        # TODO: return images

    def _load_from_generator(self, full_cmd: List[str], input: Iterator[bytes]):
        p = Popen(full_cmd, stdin=PIPE)
        for buffer_bytes in input:
            p.stdin.write(buffer_bytes)
            p.stdin.flush()
        p.stdin.close()
        exit_code = p.wait()
        if exit_code != 0:
            raise DockerException(full_cmd, exit_code)

    def list(self) -> List[Image]:
        """Returns the list of Docker images present on the machine.

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

    def prune(self):
        """Not yet implemented"""
        raise NotImplementedError

    def pull(self, image_name: str, quiet: bool = False) -> Image:
        """Pull a docker image

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
