from __future__ import annotations

import json
import warnings
from datetime import datetime
from multiprocessing.pool import ThreadPool
from pathlib import Path
from subprocess import PIPE, Popen
from typing import Any, Dict, Iterator, List, Optional, Union, overload

import python_on_whales.components.buildx.cli_wrapper
from python_on_whales.client_config import (
    ClientConfig,
    DockerCLICaller,
    ReloadableObjectFromJson,
)
from python_on_whales.components.container.cli_wrapper import (
    ContainerCLI,
    ContainerConfig,
)
from python_on_whales.components.image.models import (
    ImageGraphDriver,
    ImageInspectResult,
    ImageRootFS,
)
from python_on_whales.exceptions import DockerException, NoSuchImage
from python_on_whales.utils import (
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
        json_str = run(self.docker_cmd + ["image", "inspect", reference])
        return json.loads(json_str)[0]

    def _parse_json_object(self, json_object: Dict[str, Any]) -> ImageInspectResult:
        return ImageInspectResult(**json_object)

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
    ) -> ContainerConfig:
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
    ) -> ContainerConfig:
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
    def variant(self) -> str:
        return self._get_inspect_result().variant

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

    def __repr__(self):
        return f"python_on_whales.Image(id='{self.id[:20]}', tags={self.repo_tags})"

    def remove(self, force: bool = False, prune: bool = True):
        """Remove this Docker image.

        See the [`docker.image.remove`](../sub-commands/image.md#python_on_whales.components.image.cli_wrapper.ImageCLI.remove) command for
        information about the arguments.
        """
        ImageCLI(self.client_config).remove(self, force, prune)

    def save(self, output: Optional[ValidPath] = None) -> Optional[Iterator[bytes]]:
        """Saves this Docker image in a tar.

        See the [`docker.image.save`](../sub-commands/image.md#python_on_whales.components.image.cli_wrapper.ImageCLI.save) command for
        information about the arguments.
        """
        return ImageCLI(self.client_config).save(self, output)

    def tag(self, new_tag: str) -> None:
        """Add a tag to a Docker image.

        See the [`docker.image.tag`](../sub-commands/image.md#python_on_whales.components.image.cli_wrapper.ImageCLI.tag) command for
        information about the arguments.
        """
        return ImageCLI(self.client_config).tag(self, new_tag)

    def copy_from(
        self, path_in_image: ValidPath, destination: ValidPath, pull: str = "missing"
    ):
        """Copy a file from a docker image in the local filesystem.

        See the `docker.image.copy_from` command for information about the arguments.
        """
        return ImageCLI(self.client_config).copy_from(
            self, path_in_image, destination, pull
        )

    def copy_to(
        self,
        local_path: ValidPath,
        path_in_image: ValidPath,
        new_tag: Optional[str] = None,
        pull: str = "missing",
    ) -> Image:
        """Copy a file from the local filesystem in a docker image to create a new
        docker image.

        As if you did a dockerfile with a COPY instruction.

        See the `docker.image.copy_to` command for information about the arguments.
        """
        return ImageCLI(self.client_config).copy_to(
            self, local_path, path_in_image, new_tag, pull
        )

    def exists(self) -> bool:
        """Returns `True` if the docker image exists and `False` if it doesn't exists.

        Note that you might have done `docker.image.remove("some_tag")` and the image
        might still exists because python-on-whales references images by id, not by tag.

         See the `docker.image.exists` command for information about the arguments.
        """
        return ImageCLI(self.client_config).exists(self.id)


ValidImage = Union[str, Image]


class ImageCLI(DockerCLICaller):
    def __init__(self, client_config: ClientConfig):
        super().__init__(client_config)
        self.build = python_on_whales.components.buildx.cli_wrapper.BuildxCLI(
            client_config
        ).build

    def legacy_build(
        self,
        context_path: ValidPath,
        add_hosts: Dict[str, str] = {},
        build_args: Dict[str, str] = {},
        cache: bool = True,
        file: Optional[ValidPath] = None,
        labels: Dict[str, str] = {},
        network: Optional[str] = None,
        pull: bool = False,
        tags: Union[str, List[str]] = [],
        target: Optional[str] = None,
    ) -> python_on_whales.components.image.cli_wrapper.Image:
        """Build a Docker image with the old Docker builder (meaning not using buildx/buildkit)

        As the name implies this is a legacy building method. Users are strongly encouraged to use
        `docker.build()` instead. The legacy builder will not be available in docker v22.06 and above.

        This function also won't run the legacy builder if the environment variable
        `DOCKER_BUILDKIT` is set to `1` or if you had run previously `docker buildx install` from bash
        or `docker.buildx.install()` from Python.

        Some resources on why moving to buildx/buildkit is necessary:

        * [Proposal: make BuildKit the default builder on Linux](https://github.com/moby/moby/issues/40379)
        * [Deprecated Engine Features: Legacy builder for Linux images](https://github.com/docker/cli/blob/master/docs/deprecated.md#legacy-builder-for-linux-images)

        A `python_on_whales.Image` is returned, even when using multiple tags.
        That is because it will produce a single image with multiple tags.

        Parameters:
            context_path: The path of the build context. Defaults to the current working directory
            add_hosts: Hosts to add. `add_hosts={"my_host1": "192.168.32.35"}`
            build_args: The build arguments.
                ex `build_args={"PY_VERSION": "3.7.8", "UBUNTU_VERSION": "20.04"}`.
            cache: Whether or not to use the cache, defaults to True
            file: The path of the Dockerfile, defaults to `context_path/Dockerfile`
            labels: Dict of labels to add to the image.
                `labels={"very-secure": "1", "needs-gpu": "0"}` for example.
            network: which network to use when building the Docker image
            pull: Always attempt to pull a newer version of the image
            tags: Tag or tags to put on the resulting image.
            target: Set the target build stage to build.

        # Returns
            A `python_on_whales.Image`
        """
        # to make it easier to write and read tests, the tests of this function
        # are also grouped with the tests of "docker.build()".
        tags = to_list(tags)
        full_cmd = self.docker_cmd + ["build", "--quiet"]

        full_cmd.add_args_list(
            "--add-host", format_dict_for_cli(add_hosts, separator=":")
        )
        full_cmd.add_args_list("--build-arg", format_dict_for_cli(build_args))
        full_cmd.add_args_list("--label", format_dict_for_cli(labels))
        full_cmd.add_flag("--pull", pull)
        full_cmd.add_simple_arg("--file", file)
        full_cmd.add_simple_arg("--target", target)
        full_cmd.add_simple_arg("--network", network)
        full_cmd.add_flag("--no-cache", not cache)
        full_cmd.add_args_list("--tag", tags)

        docker_image = python_on_whales.components.image.cli_wrapper.ImageCLI(
            self.client_config
        )
        full_cmd.append(context_path)
        image_id = run(full_cmd).splitlines()[-1].strip()
        return docker_image.inspect(image_id)

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

        Parameters:
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
        """Creates a `python_on_whales.Image` object.

        # Returns
            `python_on_whales.Image`, or `List[python_on_whales.Image]` if the input
            was a list of strings.

        # Raises
            `python_on_whales.exceptions.NoSuchImage` if one of the images does not exists.

        """
        if isinstance(x, list):
            return [Image(self.client_config, identifier) for identifier in x]
        else:
            return Image(self.client_config, x)

    def exists(self, x: str) -> bool:
        """Returns `True` if the image exists. `False` otherwise.

         It's just calling `docker.image.inspect(...)` and verifies that it doesn't throw
         a `python_on_whales.exceptions.NoSuchImage`.

        # Returns
            A `bool`
        """
        try:
            self.inspect(x)
        except NoSuchImage:
            return False
        else:
            return True

    def load(
        self, input: Union[ValidPath, bytes, Iterator[bytes]], quiet: bool = False
    ) -> List[str]:
        """Loads one or multiple Docker image(s) from a tar or an iterator of `bytes`.

        Alias: `docker.load(...)`

        Parameters:
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

    def list(
        self,
        repository_or_tag: Optional[str] = None,
        filters: Dict[str, str] = {},
        all: bool = False,
    ) -> List[Image]:
        """Returns the list of Docker images present on the machine.

        Alias: `docker.images()`

        Note that each image may have multiple tags.

        # Returns
            A `List[python_on_whales.Image]` object.
        """
        # previously the signature was
        # def list(self,filters: Dict[str, str] = {}) -> List[Image]:
        # so to avoid breakages when people used positional arguments, we can check the types and send a warning
        if isinstance(repository_or_tag, dict):
            # after a while, we can convert that to an error. No hurry though.
            warnings.warn(
                f"You are calling docker.image.list({repository_or_tag}) with the filter as the first argument."
                f"Since Python-on-whales v0.51.0, the first argument has be changed to `repository_or_tag`."
                f"To fix this warning, please add the filters keyword argument, "
                f"like so: docker.image.list(filters={repository_or_tag}) ",
                DeprecationWarning,
            )
            filters = repository_or_tag
            repository_or_tag = None

        full_cmd = self.docker_cmd + [
            "image",
            "list",
            "--quiet",
            "--no-trunc",
        ]
        full_cmd.add_args_list("--filter", format_dict_for_cli(filters))
        full_cmd.add_flag("--all", all)

        if repository_or_tag is not None:
            full_cmd.append(repository_or_tag)

        ids = run(full_cmd).splitlines()
        # the list of tags is bigger than the number of images. We uniquify
        ids = set(ids)

        return [Image(self.client_config, x, is_immutable_id=True) for x in ids]

    def prune(self, all: bool = False, filter: Dict[str, str] = {}) -> str:
        """Remove unused images

        Parameters:
            all: Remove all unused images, not just dangling ones
            filter: Provide filter values (e.g. `{"until": "<timestamp>"}`)

        Returns:
            The output of the CLI (the layers removed).
        """
        full_cmd = self.docker_cmd + ["image", "prune", "--force"]
        full_cmd.add_flag("--all", all)
        full_cmd.add_args_list("--filter", format_dict_for_cli(filter))
        return run(full_cmd)

    def pull(
        self,
        x: Union[str, List[str]],
        quiet: bool = False,
        platform: Optional[str] = None,
    ) -> Union[Image, List[Image]]:
        """Pull one or more docker image(s)

        Alias: `docker.pull(...)`

        Parameters:
            x: The image name(s) . Can be a string or a list of strings. In case of
                list, multithreading is used to pull the images.
                The progress bars might look strange as multiple
                processes are drawing on the terminal at the same time.
            quiet: If you don't want to see the progress bars.
            platform: If you want to enforce a platform.

        Returns:
            The Docker image loaded (`python_on_whales.Image` object).
            If a list was passed as input, then a `List[python_on_whales.Image]` will
            be returned.
        """

        if x == []:
            return []
        elif isinstance(x, str):
            return self._pull_single_tag(x, quiet=quiet, platform=platform)
        elif isinstance(x, list) and len(x) == 1:
            return [self._pull_single_tag(x[0], quiet=quiet, platform=platform)]
        elif len(x) >= 2:
            pool = ThreadPool(4)
            generator = self._generate_args_pull(x, quiet, platform)
            all_images = pool.starmap(self._pull_single_tag, generator)
            pool.close()
            pool.join()
            return all_images

    def _generate_args_pull(
        self, _list: List[str], quiet: bool, platform: Optional[str] = None
    ):
        for tag in _list:
            yield tag, quiet, platform

    def _pull_single_tag(
        self, image_name: str, quiet: bool, platform: Optional[str] = None
    ):
        full_cmd = self.docker_cmd + ["image", "pull"]

        if quiet:
            full_cmd.append("--quiet")

        if platform:
            full_cmd.append(f"--platform={platform}")

        full_cmd.append(image_name)
        run(full_cmd, capture_stdout=quiet, capture_stderr=quiet)
        return Image(self.client_config, image_name)

    def push(self, x: Union[str, List[str]], quiet: bool = False):
        """Push a tag or a repository to a registry

        Alias: `docker.push(...)`

        Parameters:
            x: Tag(s) or repo(s) to push. Can be a string or a list of strings.
                If it's a list of string, python-on-whales will push all the images with
                multiple threads. The progress bars might look strange as multiple
                processes are drawing on the terminal at the same time.
            quiet: If you don't want to see the progress bars.

        # Raises
            `python_on_whales.exceptions.NoSuchImage` if one of the images does not exists.
        """
        x = to_list(x)

        # this is just to raise a correct exception if the images don't exist
        self.inspect(x)

        if x == []:
            return
        elif len(x) == 1:
            self._push_single_tag(x[0], quiet=quiet)
        elif len(x) >= 2:
            pool = ThreadPool(4)
            generator = self._generate_args_push(x, quiet)
            pool.starmap(self._push_single_tag, generator)
            pool.close()
            pool.join()

    def _generate_args_push(self, _list: List[str], quiet: bool):
        for tag in _list:
            yield tag, quiet

    def _push_single_tag(self, tag_or_repo: str, quiet: bool):
        full_cmd = self.docker_cmd + ["image", "push"]

        if quiet:
            full_cmd.append("--quiet")

        full_cmd.append(tag_or_repo)
        run(full_cmd, capture_stdout=quiet, capture_stderr=quiet)

    def remove(
        self,
        x: Union[ValidImage, List[ValidImage]],
        force: bool = False,
        prune: bool = True,
    ):
        """Remove one or more docker images.

        Parameters:
            x: Single image or list of Docker images to remove. You can use tags or
                `python_on_whales.Image` objects.
            force: Force removal of the image
            prune: Delete untagged parents

        # Raises
            `python_on_whales.exceptions.NoSuchImage` if one of the images does not exists.

        """

        full_cmd = self.docker_cmd + ["image", "rm"]
        full_cmd.add_flag("--force", force)
        full_cmd.add_flag("--no-prune", not prune)
        if x == []:
            return
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

        Parameters:
            images: Single docker image or list of docker images to save
            output: Path of the tar archive to produce. If `output` is None, a generator
                of bytes is produced. It can be used to stream those bytes elsewhere,
                to another Docker daemon for example.

        # Returns
            `Optional[Iterator[bytes]]`. If output is a path, nothing is returned.

        # Raises
            `python_on_whales.exceptions.NoSuchImage` if one of the images does not exists.

        # Example

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
        images = to_list(images)

        # trigger an exception early
        self.inspect(images)

        if output is not None:
            full_cmd += ["--output", str(output)]

        full_cmd += images
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
            stderr = p.stderr.read()
            if "No such image" in stderr.decode():
                raise NoSuchImage(full_cmd, exit_code, stderr=stderr)
            raise DockerException(full_cmd, exit_code, stderr=stderr)

    def tag(self, source_image: Union[Image, str], new_tag: str):
        """Adds a tag to a Docker image.

        Alias: `docker.tag(...)`

        Parameters:
            source_image: The Docker image to tag. You can use a tag to reference it.
            new_tag: The tag to add to the Docker image.

        # Raises
            `python_on_whales.exceptions.NoSuchImage` if the image does not exists.
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
        self,
        image: ValidImage,
        path_in_image: ValidPath,
        destination: ValidPath,
        pull: str = "missing",
    ):
        with ContainerCLI(self.client_config).create(image, pull=pull) as tmp_container:
            tmp_container.copy_from(path_in_image, destination)

    def copy_to(
        self,
        base_image: ValidImage,
        local_path: ValidPath,
        path_in_image: ValidPath,
        new_tag: Optional[str] = None,
        pull: str = "missing",
    ) -> Image:
        with ContainerCLI(self.client_config).create(
            base_image, pull=pull
        ) as tmp_container:
            tmp_container.copy_to(local_path, path_in_image)
            return tmp_container.commit(tag=new_tag)
