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

    def remove(self, builder: Union[Builder, str]) -> str:
        full_cmd = self.docker_cmd + ["buildx", "rm"]

        full_cmd.append(str(builder))
        return run(full_cmd)

    def build(
        self,
        context_path: ValidPath,
        file: Optional[ValidPath] = None,
        network: Optional[str] = None,
        cache: bool = True,
        output: Optional[Dict[str, str]] = None,
        platforms: Optional[List[str]] = None,
        progress: str = "auto",
        pull: bool = False,
        push: bool = False,
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
            progress:Set type of progress output (auto, plain, tty).
                Use plain to keep the container output on screen
            pull: Always attempt to pull a newer version of the image
            push: Shorthand for `output={"type": "registry"}`.
            target: Set the target build stage to build.
            tags: Tag or tags to put on the resulting image.
        """

        full_cmd = self.docker_cmd + ["buildx", "build"]

        if progress != "auto":
            full_cmd += ["--progress", progress]

        full_cmd.add_flag("--pull", pull)
        full_cmd.add_flag("--push", push)
        full_cmd.add_simple_arg("--file", file)
        full_cmd.add_simple_arg("--target", target)
        if output is not None:
            full_cmd += ["--output", ",".join(output)]
        if platforms is not None:
            full_cmd += ["--platform", ",".join(platforms)]
        full_cmd.add_simple_arg("--network", network)
        full_cmd.add_flag("--no-cache", not cache)

        for tag in to_list(tags):
            full_cmd += ["--tag", tag]

        full_cmd.append(context_path)

        run(full_cmd, capture_stderr=False)
        if tags == []:
            return None
        else:
            return python_on_whales.components.image.Image(
                self.client_config, to_list(tags)[0]
            )
