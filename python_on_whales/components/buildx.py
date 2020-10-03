from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Union

import python_on_whales.components.image
from python_on_whales.client_config import (
    ClientConfig,
    DockerCLICaller,
    ReloadableObject,
)
from python_on_whales.utils import ValidPath, run, to_list


@dataclass
class BuilderInspectResult:
    name: str
    driver: str

    @classmethod
    def from_str(cls, string):
        string = string.strip()
        result_dict = {}
        for line in string.splitlines():
            if line.startswith("Name:") and "name" not in result_dict:
                result_dict["name"] = line.split(":")[1].strip()
            if line.startswith("Driver:"):
                result_dict["driver"] = line.split(":")[1].strip()

        return cls(**result_dict)


class Builder(ReloadableObject):
    def __init__(
        self, client_config: ClientConfig, reference: str, is_immutable_id=False
    ):
        super().__init__(client_config, "name", reference, is_immutable_id)

    def _fetch_and_parse_inspect_result(self, reference: str) -> BuilderInspectResult:
        inspect_str = run(self.docker_cmd + ["buildx", "inspect", reference])
        return BuilderInspectResult.from_str(inspect_str)

    @property
    def name(self) -> str:
        return self._get_immutable_id()

    @property
    def driver(self) -> str:
        return self._get_inspect_result().driver


class BuildxCLI(DockerCLICaller):
    def bake(
        self,
        targets: Union[str, List[str]],
        files: Union[ValidPath, List[ValidPath]] = [],
        cache: bool = True,
        load: bool = False,
        pull: bool = False,
        push: bool = False,
        set: List[str] = [],
    ) -> None:
        """Bake is similar to make, it allows you to build things declared in a file.

        For example it allows you to build multiple docker image in parallel.

        The CLI docs is [here](https://github.com/docker/buildx#buildx-bake-options-target)
        and it contains a lot more information.

        # Arguments
            targets: Targets or groups of targets to build.
            files: Build definition file(s)
            cache: Whether to use the cache or not.
            load: Shorthand for `set=["*.output=type=docker"]`
            pull: Always try to pull the newer version of the image
            push: Shorthand for `set=["*.output=type=registry"]`
            set: A list of overrides in the form `"targetpattern.key=value"`.
        """
        full_cmd = self.docker_cmd + ["buildx", "bake"]

        full_cmd.add_flag("--no-cache", not cache)
        full_cmd.add_flag("--load", load)
        full_cmd.add_flag("--pull", pull)
        full_cmd.add_flag("--push", push)
        for file in to_list(files):
            full_cmd.add_simple_arg("--file", file)
        for override in set:
            full_cmd.add_simple_arg("--set", override)
        run(full_cmd + to_list(targets), capture_stderr=False)

    def create(self, context_or_endpoint: Optional[str] = None, use: bool = False):
        full_cmd = self.docker_cmd + ["buildx", "create"]

        if use:
            full_cmd.append("--use")

        if context_or_endpoint is not None:
            full_cmd.append(context_or_endpoint)
        return Builder(self.client_config, run(full_cmd))

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

    def remove(self, builder: Union[Builder, str]):
        """Remove a builder

        # Arguments
            builder: The builder to remove
        """
        full_cmd = self.docker_cmd + ["buildx", "rm"]

        full_cmd.append(str(builder))
        run(full_cmd)

    def build(
        self,
        context_path: ValidPath,
        file: Optional[ValidPath] = None,
        network: Optional[str] = None,
        cache: bool = True,
        output: Optional[Dict[str, str]] = None,
        platforms: Optional[List[str]] = None,
        progress: Union[str, bool] = "auto",
        pull: bool = False,
        push: bool = False,
        secrets: Union[str, List[str]] = [],
        tags: Union[str, List[str]] = [],
        target: Optional[str] = None,
    ) -> Optional[python_on_whales.components.image.Image]:
        """Build a Docker image with builkit as backend.

        A `python_on_whales.Image` is returned, even when using multiple tags.
        That is because it will produce a single image with multiple tags.

        # Arguments
            context_path: The path of the build context.
            file: The path of the Dockerfile
            network: which network to use when building the Docker image
            cache: Whether or not to use the cache
            output: Output destination
                (format: `output={"type": "local", "dest": "path"}`
            platforms: List of target platforms when building the image. Ex:
                `platforms=["linux/amd64", "linux/arm64"]`
            progress:Set type of progress output (auto, plain, tty, or False).
                Use plain to keep the container output on screen
            pull: Always attempt to pull a newer version of the image
            push: Shorthand for `output={"type": "registry"}`.
            secrets: One or more secrets passed as string(s). For example
                `secrets="id=aws,src=/home/my_user/.aws/credentials"`
            target: Set the target build stage to build.
            tags: Tag or tags to put on the resulting image.
        """

        full_cmd = self.docker_cmd + ["buildx", "build"]

        if progress != "auto" and isinstance(progress, str):
            full_cmd += ["--progress", progress]

        full_cmd.add_flag("--pull", pull)
        full_cmd.add_flag("--push", push)
        full_cmd.add_simple_arg("--file", file)
        full_cmd.add_simple_arg("--target", target)
        for secret in to_list(secrets):
            full_cmd += ["--secret", secret]
        if output is not None:
            full_cmd += ["--output", ",".join(output)]
        if platforms is not None:
            full_cmd += ["--platform", ",".join(platforms)]
        full_cmd.add_simple_arg("--network", network)
        full_cmd.add_flag("--no-cache", not cache)

        for tag in to_list(tags):
            full_cmd += ["--tag", tag]

        full_cmd.append(context_path)

        run(full_cmd, capture_stderr=progress is False)
        if tags == []:
            return None
        else:
            return python_on_whales.components.image.Image(
                self.client_config, to_list(tags)[0]
            )
