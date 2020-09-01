from datetime import datetime
from pathlib import Path
from subprocess import PIPE, STDOUT, Popen
from typing import Any, Dict, List, Optional, Union

import pydantic
from typeguard import typechecked

from .utils import DockerException, ValidPath, run, to_list


class Image:
    def __init__(self, id_sha256: Optional[str] = None, tag: Optional[str] = None):

        if id_sha256 is not None and tag is not None:
            raise ValueError("id_sha256 and tag cannot be used together.")

        if id_sha256 is None and tag is None:
            raise ValueError("At lease one of the id or tag must be specified.")

        if id_sha256 is not None:
            self.sha256 = id_sha256

        if tag is not None:
            raise NotImplementedError

    def __str__(self):
        return self.sha256


class ImageCLI:
    def __init__(self, docker_cmd: List[str]):
        self.docker_cmd = docker_cmd

    def _make_cli_cmd(self) -> List[str]:
        return self.docker_cmd + ["image"]

    @typechecked
    def pull(self, image_name: str, quiet: bool = False):
        full_cmd = self._make_cli_cmd() + ["pull"]

        if quiet:
            full_cmd.append("--quiet")

        full_cmd.append(image_name)
        run(full_cmd, capture_stdout=quiet, capture_stderr=quiet)

    @typechecked
    def push(self, image_or_repo: str, quiet: bool = False):
        full_cmd = self._make_cli_cmd() + ["push"]

        full_cmd.append(image_or_repo)
        run(full_cmd, capture_stdout=quiet, capture_stderr=quiet)

    @typechecked
    def save(
        self,
        images: Union[Image, str, List[Union[Image, str]]],
        output: Optional[ValidPath] = None,
    ):
        # TODO: save to bytes

        full_cmd = self._make_cli_cmd() + ["save"]

        if output is not None:
            full_cmd += ["--output", str(output)]

        for image in to_list(images):
            full_cmd.append(str(image))
        if output is None:
            # we stream the bytes
            return self._save_generator(full_cmd)
        else:
            run(full_cmd)

    def _save_generator(self, full_cmd):
        p = Popen(full_cmd, stdout=PIPE, stderr=PIPE)
        for line in p.stdout:
            yield line
        exit_code = p.wait(0.1)
        if exit_code != 0:
            raise DockerException(full_cmd, exit_code, stderr=p.stderr.read())

    @typechecked
    def load(self, input: ValidPath, quiet: bool = False):
        # TODO: load from bytes
        full_cmd = self._make_cli_cmd() + ["load", "--input", str(input)]

        if quiet:
            full_cmd.append("--quiet")

        run(full_cmd)
        # TODO: return images

    @typechecked
    def remove(self, x: Union[str, List[str]]) -> List[str]:
        full_cmd = self._make_cli_cmd() + ["remove"]
        if isinstance(x, str):
            full_cmd.append(x)
        if isinstance(x, list):
            full_cmd += x

        return run(full_cmd).split("\n")


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
    Env: List[str]
    Cmd: List[str]
    Image: str
    Volume: Optional[List[str]]
    WorkingDir: Path
    Entrypoint: List[str]
    OnBuild: List[str]
    Labels: Optional[List[str]]


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
