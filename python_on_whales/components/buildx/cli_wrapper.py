from __future__ import annotations

import json
import tempfile
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Iterator, List, Literal, Optional, Union

import python_on_whales.components.image.cli_wrapper
from python_on_whales.client_config import (
    ClientConfig,
    DockerCLICaller,
    ReloadableObject,
)
from python_on_whales.components.buildx.imagetools.cli_wrapper import ImagetoolsCLI
from python_on_whales.components.buildx.models import BuilderInspectResult
from python_on_whales.utils import (
    ValidPath,
    format_dict_for_cli,
    run,
    stream_stdout_and_stderr,
    to_list,
)


class GetImageMethod(Enum):
    TAG = 1
    IIDFILE = 2


class Builder(ReloadableObject):
    def __init__(
        self,
        client_config: ClientConfig,
        reference: Optional[str],
        is_immutable_id=False,
    ):
        super().__init__(client_config, "name", reference, is_immutable_id)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.remove()

    def _fetch_and_parse_inspect_result(
        self, reference: Optional[str]
    ) -> BuilderInspectResult:
        full_cmd = self.docker_cmd + ["buildx", "inspect"]
        if reference is not None:
            full_cmd.append(reference)
        inspect_str = run(full_cmd)
        return BuilderInspectResult.from_str(inspect_str)

    @property
    def name(self) -> str:
        return self._get_immutable_id()

    @property
    def driver(self) -> str:
        return self._get_inspect_result().driver

    @property
    def status(self) -> str:
        return self._get_inspect_result().status

    @property
    def platforms(self) -> List[str]:
        return self._get_inspect_result().platforms

    def __repr__(self):
        return f"python_on_whales.Builder(name='{self.name}', driver='{self.driver}')"

    def remove(self):
        """Removes this builder. After this operation the builder cannot be used anymore.

        If you use the builder as a context manager, it will call this function when
        you exit the context manager.

        ```python
        from python_on_whales import docker

        buildx_builder = docker.buildx.create(use=True)
        with buildx_builder:
            docker.build(".")

        # now the variable buildx_builder is not usable since we're out of the context manager.
        # the .remove() method was called behind the scenes
        # since it was the current builder, 'default' is now the current builder.
        ```

        """
        BuildxCLI(self.client_config).remove(self)


ValidBuilder = Union[str, Builder]


class BuildxCLI(DockerCLICaller):
    def __init__(self, client_config: ClientConfig):
        super().__init__(client_config)
        self.imagetools = ImagetoolsCLI(self.client_config)

    def bake(
        self,
        targets: Union[str, List[str]] = [],
        builder: Optional[ValidBuilder] = None,
        files: Union[ValidPath, List[ValidPath]] = [],
        load: bool = False,
        cache: bool = True,
        print: bool = False,
        progress: Literal["auto", "plain", "tty", False] = "auto",
        pull: bool = False,
        push: bool = False,
        set: Dict[str, str] = {},
        variables: Dict[str, str] = {},
        stream_logs: bool = False,
    ) -> Union[Dict[str, Dict[str, Dict[str, Any]]], Iterator[str]]:
        """Bake is similar to make, it allows you to build things declared in a file.

        For example it allows you to build multiple docker image in parallel.

        The CLI docs is [here](https://github.com/docker/buildx#buildx-bake-options-target)
        and it contains a lot more information.

        Parameters:
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
        env = dict(variables)
        if print:
            if stream_logs:
                ValueError(
                    "Getting the config of the bake and streaming "
                    "logs at the same time is not possible."
                )
            return json.loads(run(full_cmd + targets, env=env))
        elif stream_logs:
            return stream_buildx_logs(full_cmd + targets, env=env)
        else:
            run(full_cmd + targets, capture_stderr=progress is False, env=env)
            return json.loads(run(full_cmd + ["--print"] + targets, env=env))

    def build(
        self,
        context_path: ValidPath,
        add_hosts: Dict[str, str] = {},
        allow: List[str] = [],
        attest: Optional[Dict[str, str]] = None,
        build_args: Dict[str, str] = {},
        build_contexts: Dict[str, Union[str, ValidPath]] = {},
        builder: Optional[ValidBuilder] = None,
        cache: bool = True,
        # TODO: cache_filters
        cache_from: Union[str, Dict[str, str], List[Dict[str, str]], None] = None,
        cache_to: Union[str, Dict[str, str], None] = None,
        # TODO: cgroup_parent
        file: Optional[ValidPath] = None,
        labels: Dict[str, str] = {},
        load: bool = False,
        # TODO: metadata_file
        network: Optional[str] = None,
        output: Dict[str, str] = {},
        platforms: Optional[List[str]] = None,
        progress: Literal["auto", "plain", "tty", False] = "auto",
        provenance: Union[bool, Dict[str, str], None] = None,
        pull: bool = False,
        push: bool = False,
        sbom: Union[bool, Dict[str, str], None] = None,
        secrets: Union[str, List[str]] = [],
        # TODO shm_size
        ssh: Optional[str] = None,
        tags: Union[str, List[str]] = [],
        target: Optional[str] = None,
        # TODO: ulimit
        stream_logs: bool = False,
    ) -> Union[
        None, python_on_whales.components.image.cli_wrapper.Image, Iterator[str]
    ]:
        """Build a Docker image with builkit as backend.

        Alias: `docker.build(...)`

        A `python_on_whales.Image` is returned, even when using multiple tags.
        That is because it will produce a single image with multiple tags.
        If no image is loaded into the Docker daemon (if `push=True` for ex),
        then `None` is returned.

        Parameters:
            context_path: The path of the build context.
            add_hosts: Hosts to add. `add_hosts={"my_host1": "192.168.32.35"}`
            allow: List of extra privileges.
                Eg `allow=["network.host", "security.insecure"]`
            attest: Attestation parameters. Eg `attest={"type": "sbom", "generator": "my_image"}`
            build_args: The build arguments.
                ex `build_args={"PY_VERSION": "3.7.8", "UBUNTU_VERSION": "20.04"}`.
            build_contexts: Additional build contexts.
                `build_contexts={[name]: [value], ...}`
                Supports local directories, git repositories, HTTP URL to a tarball, a docker
                image defined with a `docker-image://` prefix, and the `oci-layout://` protocol.
                ex `build_contexts={"project2": "../path/to/project2/src", "qumu-src": "https://github.com/qemu/qemu.git"}`.
            builder: Specify which builder to use.
            cache: Whether or not to use the cache
            cache_from: Works only with the container driver. Loads the cache
                (if needed) from a registry `cache_from="user/app:cache"`  or
                a directory on the client `cache_from="type=local,src=path/to/dir"`.
                It's also possible to use a dict or list of dict form for this
                argument. e.g.
                `cache_from=dict(type="local", src="path/to/dir")`
            cache_to: Works only with the container driver. Sends the resulting
                docker cache either to a registry `cache_to="user/app:cache"`,
                or to a local directory `cache_to="type=local,dest=path/to/dir"`.
                It's also possible to use a dict form for this argument. e.g.
                `cache_to=dict(type="local", dest="path/to/dir", mode="max")`
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
            provenance: Shortand for `attest={"type": "provenance"}`.
                Eg `provenance=True` or `provenance=dict(mode="max")`. `provenance=False` might be needed
                if you are having the
                issue [Default image output from buildx v0.10 cannot run on Google Cloud Run or AWS Lambda](https://github.com/docker/buildx/issues/1533)
            pull: Always attempt to pull a newer version of the image
            push: Shorthand for `output=dict(type="registry")`.
            sbom: Shorthand for `attest={"type": "sbom"}`. Eg `sbom=True`.
            secrets: One or more secrets passed as string(s). For example
                `secrets="id=aws,src=/home/my_user/.aws/credentials"`
            ssh: SSH agent socket or keys to expose to the build
                (format is `default|<id>[=<socket>|<key>[,<key>]]` as a string)
            tags: Tag or tags to put on the resulting image.
            target: Set the target build stage to build.
            stream_logs: If `True` this function will return an iterator of strings.
                You can then read the logs as they arrive.

        # Returns
            A `python_on_whales.Image` if a Docker image is loaded
            in the daemon after the build (the default behavior when
            calling `docker.build(...)`). Otherwise, `None`.
        """
        tags = to_list(tags)
        full_cmd = self.docker_cmd + ["buildx", "build"]

        if progress != "auto" and isinstance(progress, str):
            full_cmd += ["--progress", progress]

        full_cmd.add_args_list(
            "--add-host", format_dict_for_cli(add_hosts, separator=":")
        )
        full_cmd.add_args_list("--allow", allow)
        if isinstance(attest, dict):
            full_cmd.add_simple_arg("--attest", format_dict_for_buildx(attest))
        full_cmd.add_args_list("--build-arg", format_dict_for_cli(build_args))
        full_cmd.add_args_list("--build-context", format_dict_for_cli(build_contexts))
        full_cmd.add_simple_arg("--builder", builder)
        full_cmd.add_args_list("--label", format_dict_for_cli(labels))

        full_cmd.add_simple_arg("--ssh", ssh)

        if isinstance(provenance, bool):
            full_cmd.append(f"--provenance={str(provenance).lower()}")
        elif isinstance(provenance, dict):
            full_cmd.add_simple_arg("--provenance", format_dict_for_buildx(provenance))
        full_cmd.add_flag("--pull", pull)
        full_cmd.add_flag("--push", push)
        if isinstance(sbom, bool):
            full_cmd.append(f"--sbom={str(sbom).lower()}")
        elif isinstance(sbom, dict):
            full_cmd.add_simple_arg("--sbom", format_dict_for_buildx(sbom))
        full_cmd.add_flag("--load", load)
        full_cmd.add_simple_arg("--file", file)
        full_cmd.add_simple_arg("--target", target)
        if isinstance(cache_from, list):
            for item in cache_from:
                full_cmd.add_simple_arg("--cache-from", format_dict_for_buildx(item))
        elif isinstance(cache_from, dict):
            full_cmd.add_simple_arg("--cache-from", format_dict_for_buildx(cache_from))
        else:
            full_cmd.add_simple_arg("--cache-from", cache_from)
        if isinstance(cache_to, dict):
            full_cmd.add_simple_arg("--cache-to", format_dict_for_buildx(cache_to))
        else:
            full_cmd.add_simple_arg("--cache-to", cache_to)
        full_cmd.add_args_list("--secret", to_list(secrets))
        if output != {}:
            full_cmd += ["--output", format_dict_for_buildx(output)]
        if platforms is not None:
            full_cmd += ["--platform", ",".join(platforms)]
        full_cmd.add_simple_arg("--network", network)
        full_cmd.add_flag("--no-cache", not cache)
        full_cmd.add_args_list("--tag", tags)

        if stream_logs:
            if progress in (False, "tty"):
                raise ValueError(
                    "You want to stream logs, but it's not possible if a tty is used "
                    "as 'progress'. It's also not possible if 'progress' is False. "
                    "Make sure the function arguments of 'docker.build' are "
                    "coherent."
                )

            full_cmd.append(context_path)
            return stream_buildx_logs(full_cmd)

        will_load_image = self._build_will_load_image(builder, push, load, output)
        # very special_case, must be fixed https://github.com/docker/buildx/issues/420
        if (
            will_load_image
            and not tags
            and self.inspect(builder).driver == "docker-container"
        ):
            # we have no way of fetching the image because iidfile is wrong in this case.
            will_load_image = False

        if not will_load_image:
            full_cmd.append(context_path)
            run(full_cmd, capture_stderr=progress is False)
            return

        docker_image = python_on_whales.components.image.cli_wrapper.ImageCLI(
            self.client_config
        )
        if self._method_to_get_image(builder) == GetImageMethod.TAG:
            full_cmd.append(context_path)
            run(full_cmd, capture_stderr=progress is False)
            return docker_image.inspect(tags[0])
        else:
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_dir = Path(tmp_dir)
                iidfile = tmp_dir / "id_file.txt"
                full_cmd.add_simple_arg("--iidfile", iidfile)
                full_cmd.append(context_path)
                run(full_cmd, capture_stderr=progress is False)
                image_id = iidfile.read_text()
                return docker_image.inspect(image_id)

    def _build_will_load_image(
        self,
        builder: Optional[str],
        push: bool,
        load: bool,
        output: Optional[Dict[str, str]],
    ) -> bool:
        if load:
            return True
        if push:
            return False
        if output != {}:
            if output.get("type") == "docker" and "dest" not in output:
                return True
            else:
                return False

        # now load push and output are not set.
        if self.inspect(builder).driver == "docker":
            return True

        return False

    def _method_to_get_image(self, builder: Optional[str]) -> GetImageMethod:
        """Getting around https://github.com/docker/buildx/issues/420"""
        builder = self.inspect(builder)
        if builder.driver == "docker":
            return GetImageMethod.IIDFILE
        else:
            return GetImageMethod.TAG

    def create(
        self,
        context_or_endpoint: Optional[str] = None,
        buildkitd_flags: Optional[str] = None,
        config: Optional[ValidPath] = None,
        platforms: Optional[List[str]] = None,
        driver: Optional[str] = None,
        driver_options: Dict[str, str] = {},
        name: Optional[str] = None,
        use: bool = False,
    ) -> Builder:
        """Create a new builder instance

        Parameters:
            context_or_endpoint:
            buildkitd_flags: Flags for buildkitd daemon
            config: BuildKit config file
            platforms: Comma-separated list of platforms of the form OS/architecture/variant. Ex:
                `platforms=["linux/amd64", "linux/arm64"]`
            driver: Driver to use (available: [kubernetes docker docker-container])
            driver_options: Options for the driver.
                e.g `driver_options=dict(network="host")`
            name: Builder instance name
            use: Set the current builder instance to this builder

        # Returns
            A `python_on_whales.Builder` object.
        """
        full_cmd = self.docker_cmd + ["buildx", "create"]

        full_cmd.add_simple_arg("--buildkitd-flags", buildkitd_flags)
        full_cmd.add_simple_arg("--config", config)
        if platforms is not None:
            full_cmd += ["--platform", ",".join(platforms)]
        full_cmd.add_simple_arg("--driver", driver)
        if driver_options != {}:
            full_cmd.add_simple_arg(
                "--driver-opt", format_dict_for_buildx(driver_options)
            )
        full_cmd.add_simple_arg("--name", name)
        full_cmd.add_flag("--use", use)

        if context_or_endpoint is not None:
            full_cmd.append(context_or_endpoint)
        return Builder(self.client_config, run(full_cmd))

    def disk_usage(self):
        """Not yet implemented"""
        raise NotImplementedError

    def inspect(self, x: Optional[str] = None) -> Builder:
        """Returns a builder instance from the name.

        Parameters:
            x: If `None` (the default), returns the current builder. If a string is provided,
                the builder that has this name is returned.

        # Returns
            A `python_on_whales.Builder` object.
        """
        return Builder(self.client_config, x, is_immutable_id=False)

    def list(self) -> List[Builder]:
        """Returns the list of `python_on_whales.Builder` available."""
        full_cmd = self.docker_cmd + ["buildx", "ls"]
        output = run(full_cmd)
        lines = output.splitlines()
        # the first line have the headers
        lines = lines[1:]
        # if the line starts by a " ", it's not a builder, it's a node
        lines = list(filter(lambda x: not x.startswith(" "), lines))
        builders_names = [x.split(" ")[0] for x in lines]
        # in buildx 0.13.0, the "*" is added to the name, without whitespace
        builders_names = [removesuffix(x, "*") for x in builders_names]
        return [
            Builder(self.client_config, x, is_immutable_id=True) for x in builders_names
        ]

    def prune(self, all: bool = False, filters: Dict[str, str] = {}) -> None:
        """Remove build cache on the current builder.

        Parameters:
            all: Remove all cache, not just dangling layers
            filters: Filters to use, for example `filters=dict(until="24h")`
        """
        full_cmd = self.docker_cmd + ["buildx", "prune", "--force"]
        full_cmd.add_flag("--all", all)
        full_cmd.add_args_list("--filter", format_dict_for_cli(filters))
        run(full_cmd)

    def remove(self, builder: Union[Builder, str]) -> None:
        """Remove a builder

        Parameters:
            builder: The builder to remove
        """
        full_cmd = self.docker_cmd + ["buildx", "rm"]

        full_cmd.append(builder)
        run(full_cmd)

    def stop(self, builder: Optional[ValidBuilder]) -> None:
        """Stop the builder instance

        Parameters:
            builder: The builder to stop. If `None` (the default value),
                the current builder is stopped.
        """
        full_cmd = self.docker_cmd + ["buildx", "stop"]
        if builder is not None:
            full_cmd.append(builder)
        run(full_cmd)

    def use(
        self, builder: Union[Builder, str], default: bool = False, global_: bool = False
    ) -> None:
        """Set the current builder instance

        Parameters:
            builder: The builder to use
            default: Set builder as default for the current context
            global_: Builder will be used even when changing contexts
        """
        full_cmd = self.docker_cmd + ["buildx", "use"]

        full_cmd.add_flag("--default", default)
        full_cmd.add_flag("--global", global_)
        full_cmd.append(builder)
        run(full_cmd)

    def version(self) -> str:
        """Returns the docker buildx version as a string.

        ```python
        from python_on_whales import docker

        version = docker.buildx.version()
        print(version)
        # "github.com/docker/buildx v0.4.2 fb7b670b764764dc4716df3eba07ffdae4cc47b2"
        ```
        """
        full_cmd = self.docker_cmd + ["buildx", "version"]
        return run(full_cmd)

    def is_installed(self) -> bool:
        """Returns `True` if docker buildx is installed and working.

        If it's not installed, head
        to [the installation page](https://github.com/docker/buildx#installing)
        and follow the instructions.
        """
        full_cmd = self.docker_cmd + ["buildx", "--help"]
        help_output = run(full_cmd)
        return "buildx" in help_output


def removesuffix(base_string: str, suffix: str) -> str:
    """Backport of removesuffix for python <3.9.

    TODO: Remove this when we drop support for python 3.8.
    """
    if base_string.endswith(suffix):
        return base_string[: -len(suffix)]
    return base_string


def format_dict_for_buildx(options: Dict[str, str]) -> str:
    return ",".join(format_dict_for_cli(options, separator="="))


def stream_buildx_logs(full_cmd: list, env: Dict[str, str] = None) -> Iterator[str]:
    for origin, value in stream_stdout_and_stderr(full_cmd, env=env):
        yield value.decode(errors="replace")
