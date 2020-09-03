from typing import Dict, List, Optional, Union

from typeguard import typechecked

from docker_cli_wrapper.client_config import (
    ClientConfig,
    DockerCLICaller,
    ReloadableObject,
)
from docker_cli_wrapper.utils import ValidPath, run, to_list


class Builder(ReloadableObject):
    def __init__(self, client_config: ClientConfig, name: str):
        super().__init__(client_config)
        self.name = name

    def __str__(self):
        return self.name


class BuildxCLI(DockerCLICaller):
    @typechecked
    def bake(
        self,
        targets: Union[str, List[str]],
        cache: bool = True,
        load: bool = False,
        pull: bool = False,
        push: bool = False,
    ) -> None:
        full_cmd = self.docker_cmd + ["buildx", "bake"]
        if not cache:
            full_cmd.append("--no-cache")
        if load:
            full_cmd.append("--load")
        if pull:
            full_cmd.append("--pull")
        if push:
            full_cmd.append("--push")

        run(full_cmd + to_list(targets), capture_stderr=False)

    @typechecked
    def create(self, context_or_endpoint: Optional[str] = None, use: bool = False):
        full_cmd = self.docker_cmd + ["buildx", "create"]

        if use:
            full_cmd.append("--use")

        if context_or_endpoint is not None:
            full_cmd.append(context_or_endpoint)
        return Builder(self.client_config, run(full_cmd))

    @typechecked
    def use(
        self, builder: Union[Builder, str], default: bool = False, global_: bool = False
    ):
        full_cmd = self.docker_cmd + ["buildx", "use"]

        if default:
            full_cmd.append("--use")
        if global_:
            full_cmd.append("--global")

        full_cmd.append(str(builder))

        run(full_cmd)

    @typechecked
    def remove(self, builder: Union[Builder, str]) -> str:
        full_cmd = self.docker_cmd + ["buildx", "rm"]

        full_cmd.append(str(builder))
        return run(full_cmd)

    @typechecked
    def build(
        self,
        context_path: ValidPath,
        file: Optional[ValidPath] = None,
        network: Optional[str] = None,
        cache: bool = True,
        platform: Optional[str] = None,
        progress: str = "auto",
        pull: bool = False,
        push: bool = False,
        target: Optional[str] = None,
    ) -> None:

        full_cmd = self.docker_cmd + ["buildx", "build"]

        if progress != "auto":
            full_cmd += ["--progress", progress]

        if pull:
            full_cmd.append("--pull")
        if push:
            full_cmd.append("--push")

        if file is not None:
            full_cmd += ["--file", str(file)]

        if target is not None:
            full_cmd += ["--target", target]
        if platform is not None:
            full_cmd += ["--platform", platform]
        if network is not None:
            full_cmd += ["--network", network]
        if not cache:
            full_cmd.append("--no-cache")

        full_cmd.append(str(context_path))

        run(full_cmd, capture_stderr=False)
