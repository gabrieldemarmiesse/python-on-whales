import inspect
import json
from datetime import datetime
from pathlib import Path
from subprocess import PIPE, STDOUT, Popen
from typing import Any, Dict, Iterator, List, Optional, Union

import pydantic

from docker_cli_wrapper.client_config import (
    ClientConfig,
    DockerCLICaller,
    ReloadableObjectFromJson,
)
from docker_cli_wrapper.utils import DockerException, ValidPath, run, to_list

from .buildx import BuildxCLI


class ContainerConfigClass(pydantic.BaseModel):
    Hostname: str
    Domainname: str
    User: str
    AttachStdin: bool
    AttachStdout: bool
    AttachStderr: bool
    Tty: bool
    OpenStdin: bool
    StdinOnce: bool
    Env: Optional[List[str]]
    Cmd: Optional[List[str]]
    Image: str
    Volume: Optional[List[str]]
    WorkingDir: Path
    Entrypoint: Optional[List[str]]
    OnBuild: Optional[List[str]]
    Labels: Optional[Dict[str, str]]


class ImageConfigClass(pydantic.BaseModel):
    Hostname: str
    Domainname: str
    User: str
    AttachStdin: bool
    AttachStdout: bool
    AttachStderr: bool
    Tty: bool
    OpenStdin: bool
    StdinOnce: bool
    Env: List[str]
    Cmd: List[str]
    Image: str
    Volume: Optional[List[str]]
    WorkingDir: Path
    Entrypoint: List[str]
    OnBuild: List[str]
    Labels: Optional[List[str]]


class ImageInspectResult(pydantic.BaseModel):
    Id: str
    RepoTags: List[str]
    RepoDigests: List[str]
    Parent: str
    Comment: str
    Created: datetime
    Container: str
    ContainerConfig: ContainerConfigClass
    DockerVersion: str
    Author: str
    Architecture: str
    Os: str
    Size: int
    VirtualSize: int
    GraphDriver: Dict[str, Any]
    RootFS: Dict[str, Any]
    Metadata: Dict[str, str]


class Image(ReloadableObjectFromJson):
    def __init__(
        self, client_config: ClientConfig, reference: str, is_immutable_id=False
    ):
        super().__init__(client_config, "Id", reference, is_immutable_id)

    def __str__(self):
        return self.id

    def _fetch_inspect_result_json(self, reference):
        return run(self.docker_cmd + ["image", "inspect", reference])

    def _parse_json_object(self, json_object: Dict[str, Any]) -> ImageInspectResult:
        return ImageInspectResult.parse_obj(json_object)

    @property
    def id(self) -> str:
        return self._get_immutable_id()

    @property
    def repo_tags(self) -> List[str]:
        return self._get_inspect_result().RepoTags


class ImageCLI(DockerCLICaller):
    def __init__(self, client_config: ClientConfig):
        super().__init__(client_config)
        self.build = BuildxCLI(client_config).build

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
        images: Union[Image, str, List[Union[Image, str]]],
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
