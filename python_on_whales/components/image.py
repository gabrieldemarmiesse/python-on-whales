import inspect
from datetime import datetime
from pathlib import Path
from subprocess import PIPE, Popen
from typing import Any, Dict, Iterator, List, Optional, Union

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


ValidImage = Union[str, Image]


class ImageCLI(DockerCLICaller):
    def __init__(self, client_config: ClientConfig):
        super().__init__(client_config)
        self.build = python_on_whales.components.buildx.BuildxCLI(client_config).build

    def pull(self, image_name: str, quiet: bool = False) -> Image:
        full_cmd = self.docker_cmd + ["image", "pull"]

        if quiet:
            full_cmd.append("--quiet")

        full_cmd.append(image_name)
        run(full_cmd, capture_stdout=quiet, capture_stderr=quiet)
        return Image(self.client_config, image_name)

    def push(self, tag_or_repo: str, quiet: bool = False):
        full_cmd = self.docker_cmd + ["image", "push"]

        full_cmd.append(tag_or_repo)
        run(full_cmd, capture_stdout=quiet, capture_stderr=quiet)

    def save(
        self,
        images: Union[ValidImage, List[ValidImage]],
        output: Optional[ValidPath] = None,
    ) -> Optional[Iterator[bytes]]:
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

    def load(
        self, input: Union[ValidPath, bytes, Iterator[bytes]], quiet: bool = False
    ):
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

    def remove(self, x: Union[str, List[str]]) -> List[str]:
        full_cmd = self.docker_cmd + ["image", "remove"]
        if isinstance(x, str):
            full_cmd.append(x)
        if isinstance(x, list):
            full_cmd += x

        return run(full_cmd).split("\n")

    def list(self) -> List[Image]:
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

    def tag(self, source_image: Union[Image, str], new_tag: str):
        full_cmd = self.docker_cmd + [
            "image",
            "tag",
            str(source_image),
            new_tag,
        ]
        run(full_cmd)
