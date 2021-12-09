from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

import python_on_whales.components.container.cli_wrapper
from python_on_whales.client_config import DockerCLICaller
from python_on_whales.components.compose.models import ComposeConfig
from python_on_whales.utils import run, stream_stdout_and_stderr, to_list


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
        volumes: bool = False,
    ):
        """Stops and removes the containers

        # Arguments
            remove_orphans: Remove containers for services not defined in
                the Compose file.
            remove_images: Remove images used by services.
                `"local"` remove only images that don't have a custom
                tag. Possible values are `"local"` and `"all"`.
            timeout: Specify a shutdown timeout in seconds (default 10).
            volumes: Remove named volumes declared in the
                volumes section of the Compose file and anonymous
                volumes attached to containers.
        """
        full_cmd = self.docker_compose_cmd + ["down"]
        full_cmd.add_flag("--remove-orphans", remove_orphans)
        full_cmd.add_simple_arg("--rmi", remove_images)
        full_cmd.add_simple_arg("--timeout", timeout)
        full_cmd.add_flag("--volumes", volumes)

        run(full_cmd)

    def events(self):
        """Not yet implemented"""
        raise NotImplementedError

    def exec(self):
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

    def logs(
        self,
        services: Union[str, List[str]] = [],
        tail: Optional[str] = None,
        follow: bool = False,
        no_log_prefix: bool = False,
        timestamps: bool = False,
        since: Optional[str] = None,
        until: Optional[str] = None,
        stream: bool = False,
    ):
        """View output from containers

        # Arguments
            services: One or more service(s) to view
            tail: Number of lines to show from the end of the logs for each container. (default "all")
            follow: Follow log output ***WARNING***: With this
                option, `docker.compose.logs()` will not return at all. Use it exclusively with
                `stream=True`. You can loop on the logs but the loop will never end.

            no_log_prefix: Don't print prefix in logs
            timestamps: Show timestamps
            since: Show logs since timestamp (e.g. 2013-01-02T13:23:37Z) or relative (e.g. 42m for 42 minutes)
            until: Show logs before a timestamp (e.g. 2013-01-02T13:23:37Z) or relative (e.g. 42m for 42 minutes)
            stream: Similar to the `stream` argument of `docker.run()`.
                This function will then returns and iterator that will yield a
                tuple `(source, content)` with `source` being `"stderr"` or
                `"stdout"`. `content` is the content of the line as bytes.
                Take a look at [the user guide](https://gabrieldemarmiesse.github.io/python-on-whales/user_guide/docker_run/#stream-the-output)
                to have an example of the output.
        # Returns
            `str` if `stream=False` (the default), `Iterable[Tuple[str, bytes]]`
            if `stream=True`.
        """
        full_cmd = self.docker_compose_cmd + ["logs", "--no-color"]
        full_cmd.add_simple_arg("--tail", tail)
        full_cmd.add_flag("--follow", follow)
        full_cmd.add_flag("--no-log-prefix", no_log_prefix)
        full_cmd.add_flag("--timestamps", timestamps)
        full_cmd.add_simple_arg("--since", since)
        full_cmd.add_simple_arg("--until", until)
        full_cmd += to_list(services)

        iterator = stream_stdout_and_stderr(full_cmd)
        if stream:
            return iterator
        else:
            return "".join(x[1].decode() for x in iterator)

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

    def restart(
        self,
        services: Union[str, List[str]] = [],
        timeout: Union[int, timedelta, None] = None,
    ):
        """Restart containers

        # Arguments
            services: The names of one or more services to restart (str or list of str)
            timeout: The shutdown timeout (`int` are interpreted as seconds).
                `None` means the CLI default value (10s).
                See [the docker stop docs](https://docs.docker.com/engine/reference/commandline/stop/)
                for more details about this argument.
        """
        full_cmd = self.docker_compose_cmd + ["restart"]

        if isinstance(timeout, timedelta):
            timeout = int(timeout.total_seconds())

        full_cmd.add_simple_arg("--timeout", timeout)
        full_cmd += to_list(services)
        run(full_cmd)

    def rm(
        self,
        services: Union[str, List[str]] = [],
        stop: bool = False,
        volumes: bool = False,
    ):
        """
        Removes stopped service containers

        By default, anonymous volumes attached to containers will not be removed. You
        can override this with `volumes=True`.

        Any data which is not in a volume will be lost.

        # Arguments
            services: The names of one or more services to remove (str or list of str)
            stop: Stop the containers, if required, before removing
            volumes: Remove any anonymous volumes attached to containers
        """
        full_cmd = self.docker_compose_cmd + ["rm", "--force"]
        full_cmd.add_flag("--stop", stop)
        full_cmd.add_flag("--volumes", volumes)
        full_cmd += to_list(services)
        run(full_cmd)

    def run(
        self,
        service: str,
        command: List[str] = [],
        detach: bool = False,
        # entrypoint: Optional[List[str]] = None,
        # envs: Dict[str, str] = {},
        # labels: Dict[str, str] = {},
        name: Optional[str] = None,
        tty: bool = True,
        stream: bool = False,
        dependencies: bool = True,
        publish: List[
            python_on_whales.components.container.cli_wrapper.ValidPortMapping
        ] = [],
        remove: bool = False,
        service_ports: bool = False,
        use_aliases: bool = False,
        user: Optional[str] = None,
        # volumes: bool = "todo",
        workdir: Union[None, str, Path] = None,
    ) -> Union[
        str,
        python_on_whales.components.container.cli_wrapper.Container,
        Iterable[Tuple[str, bytes]],
    ]:
        """Run a one-off command on a service.

        # Arguments
            service: The name of the service.
            command: The command to execute.
            detach: if `True`, returns immediately with the Container.
                    If `False`, returns the command stdout as string.
            name: Assign a name to the container.
            dependencies: Also start linked services.
            publish: Publish a container's port(s) to the host.
            service_ports: Enable service's ports and map them to the host.
            remove: Automatically remove the container when it exits.
            use_aliases: Use the service's network aliases in the connected network(s).
            tty: Allocate a pseudo-TTY. Allow the process to access your terminal
                to write on it.
            stream: Similar to `docker.run(..., stream=True)`.
            user: Username or UID, format: `"<name|uid>[:<group|gid>]"`
            workdir: Working directory inside the container

        # Returns:
            Optional[str]

        """

        if tty and stream:
            raise ValueError(
                "You can't set tty=True and stream=True at the same"
                "time. Their purpose are not compatible. Try setting tty=False in docker.compose.run"
            )

        if detach and stream:
            raise ValueError(
                "You can't detach and stream at the same time. It's not compatible."
            )

        if detach and tty:
            raise ValueError(
                "You can't detach and set tty=True at the same time. It's not compatible. "
                "Try setting tty=False in docker.compose.run(...)."
            )
        full_cmd = self.docker_compose_cmd + ["run"]
        full_cmd.add_flag("--detach", detach)
        full_cmd.add_simple_arg("--name", name)
        full_cmd.add_flag("--no-TTY", not tty)
        full_cmd.add_flag("--no-deps", not dependencies)
        for port_mapping in publish:
            if len(port_mapping) == 2:
                full_cmd += ["--publish", f"{port_mapping[0]}:{port_mapping[1]}"]
            else:
                full_cmd += [
                    "--publish",
                    f"{port_mapping[0]}:{port_mapping[1]}/{port_mapping[2]}",
                ]

        full_cmd.add_flag("--rm", remove)
        full_cmd.add_flag("--service-ports", service_ports)
        full_cmd.add_flag("--use-aliases", use_aliases)
        full_cmd.add_simple_arg("--user", user)
        full_cmd.add_simple_arg("--workdir", workdir)
        full_cmd.append(service)
        full_cmd += command

        if stream:
            return stream_stdout_and_stderr(full_cmd)
        else:
            result = run(full_cmd, tty=tty)
            if detach:
                Container = python_on_whales.components.container.cli_wrapper.Container
                return Container(self.client_config, result, is_immutable_id=True)
            else:
                return result

    def start(self, services: Union[str, List[str]] = []):
        """Start the specified services.

        # Arguments
            services: The names of one or more services to start
        """
        full_cmd = self.docker_compose_cmd + ["start"]
        full_cmd += to_list(services)
        run(full_cmd)

    def stop(
        self,
        services: Union[str, List[str]] = [],
        timeout: Union[int, timedelta, None] = None,
    ):
        """Stop services

        # Arguments
            services: The names of one or more services to stop (str or list of str)
            timeout: Number of seconds or timedelta (will be converted to seconds).
                Specify a shutdown timeout. Default is 10s.
        """
        if isinstance(timeout, timedelta):
            timeout = int(timeout.total_seconds())

        full_cmd = self.docker_compose_cmd + ["stop"]
        full_cmd.add_simple_arg("--timeout", timeout)
        full_cmd += to_list(services)
        run(full_cmd)

    def top(self):
        """Not yet implemented"""
        raise NotImplementedError

    def unpause(self, services: Union[str, List[str]] = []):
        """Unpause one or more services"""
        full_cmd = self.docker_compose_cmd + ["unpause"]
        full_cmd += to_list(services)
        run(full_cmd)

    def up(
        self,
        services: List[str] = [],
        build: bool = False,
        detach: bool = False,
        abort_on_container_exit: bool = False,
        scales: Dict[str, int] = {},
        attach_dependencies: bool = False,
        force_recreate: bool = False,
        no_build: bool = False,
        color: bool = True,
        log_prefix: bool = True,
        start: bool = True,
    ):
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
                Incompatible with `abort_on_container_exit=True`.
            abort_on_container_exit: If `True` stops all containers if any container was
                stopped. Incompatible with `detach=True`.
            scales: Scale SERVICE to NUM instances. Overrides
                the scale setting in the Compose file if present. For example:
                `scales={"my_service": 2, "my_other_service": 5}`.
            attach_dependencies: Attach to dependent containers.
            force_recreate: Recreate containers even if their configuration and image
                haven't changed.
            no_build: Don't build an image, even if it's missing.
            color: If `False`, it will produce monochrome output.
            log_prefix: If `False`, will not display the prefix in the logs.
            start: Start the service after creating them.

        # Returns
            `None` at the moment. The plan is to be able to capture and stream the logs later.
            It's not yet implemented.

        """
        full_cmd = self.docker_compose_cmd + ["up"]
        full_cmd.add_flag("--build", build)
        full_cmd.add_flag("--detach", detach)
        full_cmd.add_flag("--abort-on-container-exit", abort_on_container_exit)
        for service, scale in scales.items():
            full_cmd.add_simple_arg("--scale", f"{service}={scale}")
        full_cmd.add_flag("--attach-dependencies", attach_dependencies)
        full_cmd.add_flag("--force-recreate", force_recreate)
        full_cmd.add_flag("--no-build", no_build)
        full_cmd.add_flag("--no-color", not color)
        full_cmd.add_flag("--no-log-prefix", not log_prefix)
        full_cmd.add_flag("--no-start", not start)

        full_cmd += services
        run(full_cmd, capture_stdout=False)

    def version(self) -> str:
        """Returns the version of docker compose as a `str`."""
        return run(self.docker_compose_cmd + ["version"])

    def is_installed(self) -> bool:
        """Returns `True` if docker compose (the one written in Go)
        is installed and working."""
        full_cmd = self.docker_cmd + ["compose", "--help"]
        help_output = run(full_cmd)
        return "compose" in help_output
