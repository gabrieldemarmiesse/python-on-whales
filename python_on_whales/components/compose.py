from __future__ import annotations

from typing import List

from python_on_whales.client_config import DockerCLICaller
from python_on_whales.utils import run


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

    def config(self):
        """Not yet implemented"""
        raise NotImplementedError

    def create(self):
        """Not yet implemented"""
        raise NotImplementedError

    def down(self):
        """Stops and removes the containers"""
        full_cmd = self.docker_compose_cmd + ["down"]
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

    def kill(self):
        """Not yet implemented"""
        raise NotImplementedError

    def logs(self):
        """Not yet implemented"""
        raise NotImplementedError

    def pause(self):
        """Not yet implemented"""
        raise NotImplementedError

    def port(self):
        """Not yet implemented"""
        raise NotImplementedError

    def ps(self):
        """Not yet implemented"""
        raise NotImplementedError

    def pull(self):
        """Not yet implemented"""
        raise NotImplementedError

    def push(self):
        """Not yet implemented"""
        raise NotImplementedError

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

    def unpause(self):
        """Not yet implemented"""
        raise NotImplementedError

    def up(self, services: List[str] = [], build: bool = False, detach: bool = False):
        """Start the containers.

        # Arguments
            services: The services to start. If empty (default), all services are
                started.
            build: If `True`, build the docker images before starting the containers
                even if a docker image with this name already exists.
                If `False` (the default), build only the docker images that do not already
                exist.
            detach: If `True`, run the containers in the background. Only `True` is
                supported at the moment.
        """
        if not detach:
            raise NotImplementedError(
                "Only detaching containers is supported at the moment."
            )
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
