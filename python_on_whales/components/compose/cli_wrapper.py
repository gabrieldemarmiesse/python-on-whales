from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Union

import python_on_whales.components.container.cli_wrapper
from python_on_whales.client_config import DockerCLICaller
from python_on_whales.components.compose.models import ComposeConfig
from python_on_whales.utils import run, to_list


class ComposeCLI(DockerCLICaller):
    def build(self, services: List[str] = []):
        """Build services declared in a yaml compose file.

        # Arguments
            services: The services to build (as strings).
                If empty (default), all services are built.
        """
        full_cmd = self.docker_compose_cmd + ["build"]
        full_cmd += services
        run(full_cmd, capture_stdout=False)

    def config(self, return_json: bool = False) -> Union[ComposeConfig, Dict[str, Any]]:
        """Returns the configuration of the compose stack for further inspection.

        For example
        ```python
        from python_on_whales import docker
        project_config = docker.compose.config()
        print(project_config.services["my_first_service"].image)
        "redis"
        ```

        # Arguments
            return_json: If `False`, a `ComposeConfig` object will be returned, and you
                'll be able to take advantage of your IDE autocompletion. If you want the
                full json output, you may use `return_json`. In this case, you'll get
                lists and dicts corresponding to the json response, unmodified.
                It may be useful if you just want to print the config or want to access
                a field that was not in the `ComposeConfig` class.

        # Returns
            A `ComposeConfig` object if `return_json` is `False`, and a `dict` otherwise.
        """
        full_cmd = self.docker_compose_cmd + ["config", "--format", "json"]
        result = run(full_cmd, capture_stdout=True)
        if return_json:
            return json.loads(result)
        else:
            return ComposeConfig.parse_raw(result)

    def create(
        self,
        services: Union[str, List[str]] = [],
        build: bool = False,
        force_recreate: bool = False,
        no_build: bool = False,
        no_recreate=False,
    ):
        """Creates containers for a service.

        # Arguments
            build: Build images before starting containers.
            force_recreate: Recreate containers even if their configuration and
                image haven't changed.
            no_build: Don't build an image, even if it's missing.
            no_recreate: If containers already exist, don't recreate them.
                Incompatible with `force_recreate=True`.
        """
        full_cmd = self.docker_compose_cmd + ["create"]
        full_cmd.add_flag("--build", build)
        full_cmd.add_flag("--force-recreate", force_recreate)
        full_cmd.add_flag("--no-build", no_build)
        full_cmd.add_flag("--no-recreate", no_recreate)
        full_cmd += to_list(services)
        run(full_cmd, capture_stdout=False)

    def down(
        self,
        remove_orphans: bool = False,
        remove_images: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        """Stops and removes the containers

        # Arguments
            remove_orphans: Remove containers for services not defined in
                the Compose file.
            remove_images: Remove images used by services.
                `"local"` remove only images that don't have a custom
                tag. Possible values are `"local"` and `"all"`.
            timeout: Specify a shutdown timeout in seconds (default 10).
        """
        full_cmd = self.docker_compose_cmd + ["down"]
        full_cmd.add_flag("--remove-orphans", remove_orphans)
        full_cmd.add_simple_arg("--rmi", remove_images)
        full_cmd.add_simple_arg("--timeout", timeout)
        run(full_cmd)

    def events(self):
        """Not yet implemented"""
        raise NotImplementedError

    def exec(self):
        """Not yet implemented"""
        raise NotImplementedError

    def images(self):
        """Not yet implemented"""
        raise NotImplementedError

    def kill(self, services: Union[str, List[str]] = [], signal: Optional[str] = None):
        """Kills the container(s) of a service

        # Arguments
            services: One or more service(s) to kill
            signal: the signal to send to the container. Default is `"SIGKILL"`
        """
        services = to_list(services)

        full_cmd = self.docker_compose_cmd + ["kill"]
        full_cmd.add_simple_arg("--signal", signal)
        full_cmd += services
        run(full_cmd)

    def logs(self):
        """Not yet implemented"""
        raise NotImplementedError

    def pause(self, services: Union[str, List[str]] = []):
        """Pause one or more services"""
        full_cmd = self.docker_compose_cmd + ["pause"]
        full_cmd += to_list(services)
        run(full_cmd)

    def port(self):
        """Not yet implemented"""
        raise NotImplementedError

    def ps(self) -> List[python_on_whales.components.container.cli_wrapper.Container]:
        """Returns the containers that were created by the current project.

        # Returns
            A `List[python_on_whales.Container]`
        """
        full_cmd = self.docker_compose_cmd + ["ps", "--quiet"]
        result = run(full_cmd)
        ids = result.splitlines()
        # The first line might be a warning for experimental
        # See https://github.com/docker/compose-cli/issues/1108
        if len(ids) > 0 and "experimental" in ids[0]:
            ids.pop(0)

        Container = python_on_whales.components.container.cli_wrapper.Container
        return [Container(self.client_config, x, is_immutable_id=True) for x in ids]

    def pull(self, services: List[str] = []):
        """Pull service images

        # Arguments
            services: The list of services to select. Only the images of those
                services will be pulled. If no services are specified (the default
                behavior) all images of all services are pulled.
        """
        full_cmd = self.docker_compose_cmd + ["pull"]
        full_cmd += services
        run(full_cmd)

    def push(self, services: List[str] = []):
        """Push service images

        # Arguments
            services: The list of services to select. Only the images of those
                services will be pushed. If no services are specified (the default
                behavior) all images of all services are pushed.
        """
        full_cmd = self.docker_compose_cmd + ["push"]
        full_cmd += services
        run(full_cmd)

    def restart(self):
        """Not yet implemented"""
        raise NotImplementedError

    def rm(self):
        """Not yet implemented"""
        raise NotImplementedError

    def run(self):
        """Not yet implemented"""
        raise NotImplementedError

    def scale(self):
        """Not yet implemented"""
        raise NotImplementedError

    def start(self):
        """Not yet implemented"""
        raise NotImplementedError

    def stop(self):
        """Not yet implemented"""
        raise NotImplementedError

    def top(self):
        """Not yet implemented"""
        raise NotImplementedError

    def unpause(self, services: Union[str, List[str]] = []):
        """Unpause one or more services"""
        full_cmd = self.docker_compose_cmd + ["unpause"]
        full_cmd += to_list(services)
        run(full_cmd)

    def up(self, services: List[str] = [], build: bool = False, detach: bool = False):
        """Start the containers.

        Reading the logs of the containers is not yet implemented.

        # Arguments
            services: The services to start. If empty (default), all services are
                started.
            build: If `True`, build the docker images before starting the containers
                even if a docker image with this name already exists.
                If `False` (the default), build only the docker images that do not already
                exist.
            detach: If `True`, run the containers in the background. If `False` this
                function returns only when all containers have stopped.

        # Returns
            `None` at the moment. The plan is to be able to capture and stream the logs later.
            It's not yet implemented.

        """
        full_cmd = self.docker_compose_cmd + ["up"]
        full_cmd.add_flag("--detach", detach)
        full_cmd.add_flag("--build", build)

        full_cmd += services
        run(full_cmd, capture_stdout=False)

    def version(self):
        """Not yet implemented"""
        raise NotImplementedError

    def is_installed(self) -> bool:
        """Returns `True` if docker compose (the one written in Go)
        is installed and working."""
        full_cmd = self.docker_cmd + ["compose", "--help"]
        help_output = run(full_cmd)
        return "compose" in help_output
