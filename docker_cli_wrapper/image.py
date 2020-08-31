from typing import List, Union

from typeguard import typechecked

from .utils import run


class ImageCLI:
    def __init__(self, docker_cmd: List[str]):
        self.docker_cmd = docker_cmd

    def _make_cli_cmd(self) -> List[str]:
        return self.docker_cmd + ["image"]

    def pull(self, image_name, quiet=False):
        if not quiet:
            raise NotImplementedError
        full_cmd = self._make_cli_cmd() + ["pull"]

        if quiet:
            full_cmd.append("--quiet")

        full_cmd.append(image_name)
        run(full_cmd)

    @typechecked
    def remove(self, x: Union[str, List[str]]) -> List[str]:
        full_cmd = self._make_cli_cmd() + ["remove"]
        if isinstance(x, str):
            full_cmd.append(x)
        if isinstance(x, list):
            full_cmd += x

        return run(full_cmd).split("\n")


class Image:
    def __init__(self, sha256: str):
        self.sha256 = sha256
