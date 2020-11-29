from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import python_on_whales.components.image
from python_on_whales.client_config import (
    ClientConfig,
    DockerCLICaller,
    ReloadableObject,
)
from python_on_whales.utils import ValidPath, format_dict_for_cli, run, to_list


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


ValidBuilder = Union[str, Builder]


class BuildxCLI(DockerCLICaller):
    def bake(
        self,
        targets: Union[str, List[str]] = [],
        builder: Optional[ValidBuilder] = None,
        files: Union[ValidPath, List[ValidPath]] = [],
        load: bool = False,
        cache: bool = True,
        print: bool = False,
        progress: Union[str, bool] = "auto",
        pull: bool = False,
        push: bool = False,
        set: Dict[str, str] = {},
        variables: Dict[str, str] = {},
    ) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """Bake is similar to make, it allows you to build things declared in a file.

        For example it allows you to build multiple docker image in parallel.

        The CLI docs is [here](https://github.com/docker/buildx#buildx-bake-options-target)
        and it contains a lot more information.

        # Arguments
            targets: Targets or groups of targets to build.
            builder: The builder to use.
            files: Build definition file(s)
            load: Shorthand for `set=["*.output=type=docker"]`
            cache: Whether to use the cache or not.
            print: Do nothing, just returns the config.
            progress: Set type of progress output (`"auto"`, `"plain"`, `"tty"`,
                or `False`). Use plain to keep the container output on screen
            pull: Always try to pull the newer version of the image
            push: Shorthand for `set=["*.output=type=registry"]`
            set: A list of overrides in the form `"targetpattern.key=value"`.
            variables: A dict containing the values of the variables defined in the
                hcl file. See <https://github.com/docker/buildx#hcl-variables-and-functions>

        # Returns
            The configuration used for the bake (files merged + override with
            the arguments used in the function). It's the loaded json you would
            obtain by running `docker buildx bake --print --load my_target` if
            your command was `docker buildx bake --load my_target`. Some example here.


        ```python
        from python_on_whales import docker

        # returns the config used and runs the builds
        config = docker.buildx.bake(["my_target1", "my_target2"], load=True)
        assert config == {
            "target": {
                "my_target1": {
                    "context": "./",
                    "dockerfile": "Dockerfile",
                    "tags": ["pretty_image1:1.0.0"],
                    "target": "out1",
                    "output": ["type=docker"]
                },
                "my_target2": {
                    "context": "./",
                    "dockerfile": "Dockerfile",
                    "tags": ["pretty_image2:1.0.0"],
                    "target": "out2",
                    "output": ["type=docker"]
                }
            }
        }

        # returns the config only, doesn't run the builds
        config = docker.buildx.bake(["my_target1", "my_target2"], load=True, print=True)
        ```
        """
        full_cmd = self.docker_cmd + ["buildx", "bake"]

        full_cmd.add_flag("--no-cache", not cache)
        full_cmd.add_simple_arg("--builder", builder)
        full_cmd.add_flag("--load", load)
        full_cmd.add_flag("--pull", pull)
        full_cmd.add_flag("--push", push)
        full_cmd.add_flag("--print", print)
        if progress != "auto" and isinstance(progress, str):
            full_cmd += ["--progress", progress]
        for file in to_list(files):
            full_cmd.add_simple_arg("--file", file)
        full_cmd.add_args_list("--set", format_dict_for_cli(set))
        targets = to_list(targets)
        env = dict(os.environ)
        env.update(variables)
        if print:
            return json.loads(run(full_cmd + targets, env=env))
        else:
            run(full_cmd + targets, capture_stderr=progress is False, env=env)
            return json.loads(run(full_cmd + ["--print"] + targets, env=env))

    def build(
        self,
        context_path: ValidPath,
        add_hosts: Dict[str, str] = {},
        allow: List[str] = [],
        build_args: Dict[str, str] = {},
        builder: Optional[ValidBuilder] = None,
        cache: bool = True,
        cache_from: Optional[str] = None,
        cache_to: Optional[str] = None,
        file: Optional[ValidPath] = None,
        labels: Dict[str, str] = {},
        load: bool = False,
        network: Optional[str] = None,
        output: Optional[Dict[str, str]] = None,
        platforms: Optional[List[str]] = None,
        progress: Union[str, bool] = "auto",
        pull: bool = False,
        push: bool = False,
        secrets: Union[str, List[str]] = [],
        ssh: Optional[str] = None,
        tags: Union[str, List[str]] = [],
        target: Optional[str] = None,
        return_image: bool = False,
    ) -> Optional[python_on_whales.components.image.Image]:
        """Build a Docker image with builkit as backend.

        A `python_on_whales.Image` is returned, even when using multiple tags.
        That is because it will produce a single image with multiple tags.

        # Arguments
            context_path: The path of the build context.
            add_hosts: Hosts to add. `add_hosts={"my_host1": "192.168.32.35"}`
            allow: List of extra privileges.
                Eg `allow=["network.host", "security.insecure"]`
            build_args: The build arguments.
                ex `build_args={"PY_VERSION": "3.7.8", "UBUNTU_VERSION": "20.04"}`.
            builder: Specify which builder to use.
            cache: Whether or not to use the cache
            cache_from: Works only with the container driver. Loads the cache
                (if needed) from a registry `cache_from="user/app:cache"`  or
                a directory on the client `cache_from="type=local,src=path/to/dir"`.
            cache_to: Works only with the container driver. Sends the resulting
                docker cache either to a registry `cache_to="user/app:cache"`,
                or to a local directory `cache_to="type=local,dest=path/to/dir"`.
            file: The path of the Dockerfile
            labels: Dict of labels to add to the image.
                `labels={"very-secure": "1", "needs-gpu": "0"}` for example.
            load: Shortcut for `output=dict(type="docker")` If `True`,
                `docker.buildx.build` will return a `python_on_whales.Image`.
            network: which network to use when building the Docker image
            output: Output destination
                (format: `output={"type": "local", "dest": "path"}`
                Possible output types are
                `["local", "tar", "oci", "docker", "image", "registry"]`.
                See [this link](https://github.com/docker/buildx#-o---outputpath-typetypekeyvalue)
                for more details about each exporter.
            platforms: List of target platforms when building the image. Ex:
                `platforms=["linux/amd64", "linux/arm64"]`
            progress: Set type of progress output (auto, plain, tty, or False).
                Use plain to keep the container output on screen
            pull: Always attempt to pull a newer version of the image
            push: Shorthand for `output=dict(type="registry")`.
            secrets: One or more secrets passed as string(s). For example
                `secrets="id=aws,src=/home/my_user/.aws/credentials"`
            ssh: SSH agent socket or keys to expose to the build
                (format is `default|<id>[=<socket>|<key>[,<key>]]` as a string)
            tags: Tag or tags to put on the resulting image.
            target: Set the target build stage to build.
            return_image: Return the created docker image if `True`, needs
                at least one `tags`.

        # Returns
            A `python_on_whales.Image` if `return_image=True`. Otherwise, `None`.
        """

        full_cmd = self.docker_cmd + ["buildx", "build"]

        if progress != "auto" and isinstance(progress, str):
            full_cmd += ["--progress", progress]

        full_cmd.add_args_list(
            "--add-host", format_dict_for_cli(add_hosts, separator=":")
        )
        full_cmd.add_args_list("--allow", allow)
        full_cmd.add_args_list("--build-arg", format_dict_for_cli(build_args))
        full_cmd.add_simple_arg("--builder", builder)
        full_cmd.add_args_list("--label", format_dict_for_cli(labels))

        full_cmd.add_simple_arg("--ssh", ssh)

        full_cmd.add_flag("--pull", pull)
        full_cmd.add_flag("--push", push)
        full_cmd.add_flag("--load", load)
        full_cmd.add_simple_arg("--file", file)
        full_cmd.add_simple_arg("--target", target)
        full_cmd.add_simple_arg("--cache-from", cache_from)
        full_cmd.add_simple_arg("--cache-to", cache_to)
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
        if return_image:
            if to_list(tags) == []:
                raise ValueError(
                    "If you want the docker image returned, you need to specify tags."
                )
            return python_on_whales.components.image.ImageCLI(
                self.client_config
            ).inspect(to_list(tags)[0])

    def create(self, context_or_endpoint: Optional[str] = None, use: bool = False):
        full_cmd = self.docker_cmd + ["buildx", "create"]

        if use:
            full_cmd.append("--use")

        if context_or_endpoint is not None:
            full_cmd.append(context_or_endpoint)
        return Builder(self.client_config, run(full_cmd))

    def disk_usage(self):
        """Not yet implemented"""
        raise NotImplementedError

    def inspect(self):
        """Not yet implemented"""
        raise NotImplementedError

    def list(self):
        """Not yet implemented"""
        raise NotImplementedError

    def prune(self, all: bool = False, filters: Dict[str, str] = {}) -> None:
        """Remove build cache on the current builder.

        # Arguments
            all: Remove all cache, not just dangling layers
            filters: Filters to use, for example `filters=dict(until="24h")`
        """
        full_cmd = self.docker_cmd + ["buildx", "prune", "--force"]
        full_cmd.add_flag("--all", all)
        full_cmd.add_args_list("--filter", format_dict_for_cli(filters))
        run(full_cmd)

    def remove(self, builder: Union[Builder, str]):
        """Remove a builder

        # Arguments
            builder: The builder to remove
        """
        full_cmd = self.docker_cmd + ["buildx", "rm"]

        full_cmd.append(str(builder))
        run(full_cmd)

    def stop(self):
        """Not yet implemented"""
        raise NotImplementedError

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

    def version(self):
        """Not yet implemented"""
        raise NotImplementedError
