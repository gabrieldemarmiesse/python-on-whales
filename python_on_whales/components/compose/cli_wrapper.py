from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union, overload

from typing_extensions import Literal

import python_on_whales.components.container.cli_wrapper
from python_on_whales.client_config import DockerCLICaller
from python_on_whales.components.compose.models import ComposeConfig, ComposeProject
from python_on_whales.utils import (
    format_dict_for_cli,
    format_signal_arg,
    parse_ls_status_count,
    run,
    stream_stdout_and_stderr,
    to_list,
)


class ComposeCLI(DockerCLICaller):
    @overload
    def build(
        self,
        services: Union[List[str], str, None] = ...,
        build_args: Dict[str, str] = ...,
        cache: bool = ...,
        progress: Optional[str] = ...,
        pull: bool = ...,
        quiet: bool = ...,
        ssh: Optional[str] = ...,
        stream_logs: Literal[True] = ...,
    ) -> Iterable[Tuple[str, bytes]]:
        ...

    @overload
    def build(
        self,
        services: Union[List[str], str, None] = ...,
        build_args: Dict[str, str] = ...,
        cache: bool = ...,
        progress: Optional[str] = ...,
        pull: bool = ...,
        quiet: bool = ...,
        ssh: Optional[str] = ...,
        stream_logs: Literal[False] = ...,
    ) -> None:
        ...

    def build(
        self,
        services: Union[List[str], str, None] = None,
        build_args: Dict[str, str] = {},
        cache: bool = True,
        progress: Optional[str] = None,
        pull: bool = False,
        quiet: bool = False,
        ssh: Optional[str] = None,
        stream_logs: bool = False,
    ) -> Union[Iterable[Tuple[str, bytes]], None]:
        """Build services declared in a yaml compose file.

        Parameters:
            services: The services to build (as list of strings).
                If `None` (default), all services are built.
                An empty list means that nothing will be built.
            build_args: Set build-time variables for services. For example
                 `build_args={"PY_VERSION": "3.7.8", "UBUNTU_VERSION": "20.04"}`.
            cache: Set to `False` if you don't want to use the cache to build your images
            progress: Set type of progress output (auto, tty, plain, quiet) (default "auto")
            pull: Set to `True` to always attempt to pull a newer version of the
                image (in the `FROM` statements for example).
            quiet: Don't print anything
            ssh: Set SSH authentications used when building service images.
                (use `'default'` for using your default SSH Agent)
            stream_logs: If `False` this function returns None. If `True`, this
                function returns an Iterable of `Tuple[str, bytes]` where the first element
                is the type of log (`"stdin"` or `"stdout"`). The second element is the log itself,
                as bytes, you'll need to call `.decode()` if you want the logs as `str`.
                See [the streaming guide](https://gabrieldemarmiesse.github.io/python-on-whales/user_guide/docker_run/#stream-the-output) if you are
                not familiar with the streaming of logs in Python-on-whales.
        """
        if quiet and stream_logs:
            raise ValueError(
                "It's not possible to have stream_logs=True and quiet=True at the same time. "
                "Only one can be activated at a time."
            )

        full_cmd = self.docker_compose_cmd + ["build"]
        full_cmd.add_args_list("--build-arg", format_dict_for_cli(build_args))
        full_cmd.add_flag("--no-cache", not cache)
        full_cmd.add_simple_arg("--progress", progress)
        full_cmd.add_flag("--pull", pull)
        full_cmd.add_flag("--quiet", quiet)
        full_cmd.add_simple_arg("--ssh", ssh)

        if services == []:
            return
        elif services is not None:
            full_cmd += to_list(services)
        else:
            pass  # passing nothing means all services are built
        if stream_logs:
            return stream_stdout_and_stderr(full_cmd)
        else:
            run(full_cmd, capture_stdout=False)

    @overload
    def config(self, return_json: Literal[False] = ...) -> ComposeConfig:
        ...

    @overload
    def config(self, return_json: Literal[True] = ...) -> Dict[str, Any]:
        ...

    def config(self, return_json: bool = False) -> Union[ComposeConfig, Dict[str, Any]]:
        """Returns the configuration of the compose stack for further inspection.

        For example
        ```python
        from python_on_whales import docker
        project_config = docker.compose.config()
        print(project_config.services["my_first_service"].image)
        "redis"
        ```

        Parameters:
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
            return ComposeConfig(**json.loads(result))

    @overload
    def create(
        self,
        services: Union[str, List[str], None] = ...,
        build: bool = ...,
        force_recreate: bool = ...,
        no_build: bool = ...,
        no_recreate: bool = ...,
        stream_logs: Literal[True] = ...,
    ) -> Iterable[Tuple[str, bytes]]:
        ...

    @overload
    def create(
        self,
        services: Union[str, List[str], None] = ...,
        build: bool = ...,
        force_recreate: bool = ...,
        no_build: bool = ...,
        no_recreate: bool = ...,
        stream_logs: Literal[False] = ...,
    ) -> None:
        ...

    def create(
        self,
        services: Union[str, List[str], None] = None,
        build: bool = False,
        force_recreate: bool = False,
        no_build: bool = False,
        no_recreate: bool = False,
        stream_logs: bool = False,
    ) -> Union[Iterable[Tuple[str, bytes]], None]:
        """Creates containers for a service.

        Parameters:
            services: The name of the services for which the containers will
                be created. The default `None` means that the containers for all
                services will be created. A single string means we will create the
                container for a single service. A list of string means we will create
                the containers for each service in the list. An empty list means nothing
                will be created, the function call is then a no-op.
            build: Build images before starting containers.
            force_recreate: Recreate containers even if their configuration and
                image haven't changed.
            no_build: Don't build an image, even if it's missing.
            no_recreate: If containers already exist, don't recreate them.
                Incompatible with `force_recreate=True`.
            stream_logs: If `False` this function returns None. If `True`, this
                function returns an Iterable of `Tuple[str, bytes]` where the first element
                is the type of log (`"stdin"` or `"stdout"`). The second element is the log itself,
                as bytes, you'll need to call `.decode()` if you want the logs as `str`.
                See [the streaming guide](https://gabrieldemarmiesse.github.io/python-on-whales/user_guide/docker_run/#stream-the-output) if you are
                not familiar with the streaming of logs in Python-on-whales.
        """
        full_cmd = self.docker_compose_cmd + ["create"]
        full_cmd.add_flag("--build", build)
        full_cmd.add_flag("--force-recreate", force_recreate)
        full_cmd.add_flag("--no-build", no_build)
        full_cmd.add_flag("--no-recreate", no_recreate)
        if services == []:
            return
        elif services is not None:
            full_cmd += to_list(services)
        if stream_logs:
            print(full_cmd)
            return stream_stdout_and_stderr(full_cmd)
        else:
            run(full_cmd, capture_stdout=False)

    @overload
    def down(
        self,
        services: Union[List[str], str, None] = ...,
        remove_orphans: bool = ...,
        remove_images: Optional[str] = ...,
        timeout: Optional[int] = ...,
        volumes: bool = ...,
        quiet: bool = ...,
        stream_logs: Literal[True] = ...,
    ) -> Iterable[Tuple[str, bytes]]:
        ...

    @overload
    def down(
        self,
        services: Union[List[str], str, None] = ...,
        remove_orphans: bool = ...,
        remove_images: Optional[str] = ...,
        timeout: Optional[int] = ...,
        volumes: bool = ...,
        quiet: bool = ...,
        stream_logs: Literal[False] = ...,
    ) -> None:
        ...

    def down(
        self,
        services: Union[List[str], str, None] = None,
        remove_orphans: bool = False,
        remove_images: Optional[str] = None,
        timeout: Optional[int] = None,
        volumes: bool = False,
        quiet: bool = False,
        stream_logs: bool = False,
    ):
        """Stops and removes the containers

        Parameters:
            services: The services to stop. If `None` (default), all services are
                stopped. If an empty list is provided, the function call does nothing, it's
                a no-op.
            remove_orphans: Remove containers for services not defined in
                the Compose file.
            remove_images: Remove images used by services.
                `"local"` remove only images that don't have a custom
                tag. Possible values are `"local"` and `"all"`.
            timeout: Specify a shutdown timeout in seconds (default 10).
            volumes: Remove named volumes declared in the
                volumes section of the Compose file and anonymous
                volumes attached to containers.
            quiet: If `False`, send to stderr and stdout the progress spinners with
                the messages. If `True`, do not display anything.
        """
        if quiet and stream_logs:
            raise ValueError(
                "It's not possible to have stream_logs=True and quiet=True at the same time. "
                "Only one can be activated at a time."
            )

        full_cmd = self.docker_compose_cmd + ["down"]
        full_cmd.add_flag("--remove-orphans", remove_orphans)
        full_cmd.add_simple_arg("--rmi", remove_images)
        full_cmd.add_simple_arg("--timeout", timeout)
        full_cmd.add_flag("--volumes", volumes)

        if services == []:
            return
        elif services is not None:
            services = to_list(services)
            full_cmd += services

        if stream_logs:
            return stream_stdout_and_stderr(full_cmd)
        else:
            run(full_cmd, capture_stderr=quiet, capture_stdout=quiet)

    def execute(
        self,
        service: str,
        command: List[str],
        detach: bool = False,
        envs: Dict[str, str] = {},
        index: int = 1,
        tty: bool = True,
        privileged: bool = False,
        user: Optional[str] = None,
        workdir: Union[str, Path, None] = None,
    ) -> Optional[str]:
        """Execute a command in a running container.

        Parameters:
            service: The name of the service.
            command: The command to execute.
            detach: If `True`, detach from the container after the command exits. In this case,
                 nothing is returned by the function. By default, the execute command returns only when the
                 command has finished running, and the function will raise an exception `DockerException` if the command
                 exits with a non-zero exit code. If `False`, the command is executed and the stdout is returned.
            envs: A dictionary of environment variables to set in the container.
            index: The index of the container to execute the command in (default 1) if there are multiple containers for this service.
            tty: If `True`, allocate a pseudo-TTY. Use `False` to get the output of the command.
            privileged: If `True`, run the command in privileged mode.
            user: The username to use inside the container.
            workdir: The working directory inside the container.
        """
        full_cmd = self.docker_compose_cmd + ["exec"]
        full_cmd.add_flag("--detach", detach)
        for key, value in envs.items():
            full_cmd.add_simple_arg("--env", f"{key}={value}")
        full_cmd.add_simple_arg("--index", index)
        full_cmd.add_flag("--no-TTY", not tty)
        full_cmd.add_flag("--privileged", privileged)
        full_cmd.add_simple_arg("--user", user)
        full_cmd.add_simple_arg("--workdir", workdir)
        full_cmd += [service] + command
        if detach:
            run(full_cmd)
        elif tty:
            run(full_cmd, capture_stdout=False, capture_stderr=False)
        else:
            return run(full_cmd)

    def kill(
        self,
        services: Union[str, List[str]] = None,
        signal: Optional[Union[int, str]] = None,
    ):
        """Kills the container(s) of a service

        Parameters:
            services: One or more service(s) to kill. The default (`None`) is to kill all services.
                A string means the call will kill one single service. A list of service names can
                be provided to kill multiple services in one function call.
                An empty list means that no services are going to be killed, the function is then
                a no-op.
            signal: the signal to send to the container. Default is `"SIGKILL"`
        """
        full_cmd = self.docker_compose_cmd + ["kill"]
        full_cmd.add_simple_arg("--signal", format_signal_arg(signal))
        if services == []:
            return
        elif services is not None:
            full_cmd += to_list(services)
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

        Parameters:
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
                This function will then return and iterator that will yield a
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

    def pause(self, services: Union[str, List[str], None] = None):
        """Pause one or more services

        Parameters:
            services: `None` (the default) means pause all containers of all
                compose services. A string means that the call will pause the container
                of a specific service. A list of string means the call will pause
                the containers of all the services specified. So if an empty list
                is provided, then this function call is a no-op.
        """
        full_cmd = self.docker_compose_cmd + ["pause"]
        if services == []:
            return
        elif services is not None:
            full_cmd += to_list(services)
        run(full_cmd)

    def port(
        self,
        service: str,
        private_port: Union[str, int],
        index: int = 1,
        protocol: str = "tcp",
    ) -> Tuple[Optional[str], Optional[int]]:
        """Returns the public port for a port binding.

        Parameters:
            service: The name of the service.
            private_port: The private port.
            index: Index of the container if service has multiple replicas (default 1)
            protocol: tcp or udp (default "tcp").

        # Returns
            tuple with (host, port). If port is unknown, then host and port are None.
        """
        full_cmd = self.docker_compose_cmd + ["port"]
        if service == "":
            raise ValueError("Service cannot be empty")
        if private_port == "":
            raise ValueError("Private port cannot be empty")

        full_cmd.add_simple_arg("--index", index)
        full_cmd.add_simple_arg("--protocol", protocol)
        full_cmd += [service, private_port]

        result = run(full_cmd)
        if result == ":0":
            # docker compose cli joins host:str with port:int in the result. If port is unknown
            # then result has default value for the both variables (str->empty string, int -> 0)
            return None, None

        host, port = str(result).split(":")
        return host, int(port)

    def ps(
        self,
        services: Optional[List[str]] = None,
        all: bool = False,
    ) -> List[python_on_whales.components.container.cli_wrapper.Container]:
        """Returns the containers that were created by the current project.

        # Returns
            A `List[python_on_whales.Container]`
        """
        full_cmd = self.docker_compose_cmd + ["ps", "--quiet"]
        full_cmd.add_flag("--all", all)
        if services:
            full_cmd += services
        result = run(full_cmd)
        ids = result.splitlines()
        # The first line might be a warning for experimental
        # See https://github.com/docker/compose-cli/issues/1108
        if len(ids) > 0 and "experimental" in ids[0]:
            ids.pop(0)

        Container = python_on_whales.components.container.cli_wrapper.Container
        return [Container(self.client_config, x, is_immutable_id=True) for x in ids]

    def ls(
        self, all: bool = False, filters: Dict[str, str] = {}
    ) -> List[ComposeProject]:
        """Returns a list of docker compose projects

        Parameters:
            all: Results include all stopped compose projects.
            filters: Filter results based on conditions provided.

        # Returns
            A `List[python_on_whales.ComposeProject]`
        """
        full_cmd = self.docker_compose_cmd + ["ls", "--format", "json"]
        full_cmd.add_flag("--all", all)
        full_cmd.add_args_list("--filter", format_dict_for_cli(filters))

        return [
            ComposeProject(
                name=proj["Name"],
                created=parse_ls_status_count(proj["Status"], "created"),
                running=parse_ls_status_count(proj["Status"], "running"),
                restarting=parse_ls_status_count(proj["Status"], "restarting"),
                exited=parse_ls_status_count(proj["Status"], "exited"),
                paused=parse_ls_status_count(proj["Status"], "paused"),
                dead=parse_ls_status_count(proj["Status"], "dead"),
                config_files=[
                    Path(path)
                    for path in proj.get("ConfigFiles", "").split(",")
                    if "ConfigFiles" in proj
                ]
                or None,
            )
            for proj in json.loads(run(full_cmd))
        ]

    @overload
    def pull(
        self,
        services: Union[List[str], str, None] = ...,
        ignore_pull_failures: bool = ...,
        include_deps: bool = ...,
        quiet: bool = ...,
        stream_logs: Literal[True] = ...,
    ) -> Iterable[Tuple[str, bytes]]:
        ...

    @overload
    def pull(
        self,
        services: Union[List[str], str, None] = ...,
        ignore_pull_failures: bool = ...,
        include_deps: bool = ...,
        quiet: bool = ...,
        stream_logs: Literal[False] = ...,
    ) -> None:
        ...

    def pull(
        self,
        services: Union[List[str], str, None] = None,
        ignore_pull_failures: bool = False,
        include_deps: bool = False,
        quiet: bool = False,
        stream_logs: bool = False,
    ) -> Union[Iterable[Tuple[str, bytes]], None]:
        """Pull service images

        Parameters:
            services: The list of services to select. Only the images of those
                services will be pulled. If no services are specified (`None`) (the default
                behavior) all images of all services are pulled.
                If an empty list is provided, then the function call is a no-op.
            ignore_pull_failures: Pull what it can and ignores images with pull failures
            include_deps: Also pull services declared as dependencies
            quiet: By default, the progress bars are printed in stdout and stderr (both).
                To disable all output, use `quiet=True`
            stream_logs: If `False` this function returns None. If `True`, this
                function returns an Iterable of `Tuple[str, bytes]` where the first element
                is the type of log (`"stdin"` or `"stdout"`). The second element is the log itself,
                as bytes, you'll need to call `.decode()` if you want the logs as `str`.
                See [the streaming guide](https://gabrieldemarmiesse.github.io/python-on-whales/user_guide/docker_run/#stream-the-output) if you are
                not familiar with the streaming of logs in Python-on-whales.

        """
        if quiet and stream_logs:
            raise ValueError(
                "It's not possible to have stream_logs=True and quiet=True at the same time. "
                "Only one can be activated at a time."
            )
        full_cmd = self.docker_compose_cmd + ["pull"]
        full_cmd.add_flag("--ignore-pull-failures", ignore_pull_failures)
        full_cmd.add_flag("--include-deps", include_deps)
        full_cmd.add_flag("--quiet", quiet)
        if services == []:
            return
        elif services is not None:
            services = to_list(services)
            full_cmd += services
        if stream_logs:
            return stream_stdout_and_stderr(full_cmd)
        else:
            run(full_cmd, capture_stdout=False, capture_stderr=False)

    def push(self, services: Optional[List[str]] = None):
        """Push service images

        Parameters:
            services: The list of services to select. Only the images of those
                services will be pushed. If no services are specified (`None`, the default
                behavior) all images of all services are pushed.
                If an empty list is provided, then the function call is a no-op.
        """
        full_cmd = self.docker_compose_cmd + ["push"]
        if services == []:
            return
        elif services is not None:
            full_cmd += services
        run(full_cmd)

    def restart(
        self,
        services: Union[str, List[str], None] = None,
        timeout: Union[int, timedelta, None] = None,
    ):
        """Restart containers

        Parameters:
            services: The names of one or more services to restart (str or list of str).
                If the argument is not specified, `services` is `None` and all services are restarted.
                If `services` is an empty list, then the function call is a no-op.
            timeout: The shutdown timeout (`int` are interpreted as seconds).
                `None` means the CLI default value (10s).
                See [the docker stop docs](https://docs.docker.com/engine/reference/commandline/stop/)
                for more details about this argument.
        """
        full_cmd = self.docker_compose_cmd + ["restart"]

        if isinstance(timeout, timedelta):
            timeout = int(timeout.total_seconds())

        full_cmd.add_simple_arg("--timeout", timeout)
        if services == []:
            return
        elif services is not None:
            full_cmd += to_list(services)
        run(full_cmd)

    def rm(
        self,
        services: Union[str, List[str], None] = None,
        stop: bool = False,
        volumes: bool = False,
    ):
        """
        Removes stopped service containers

        By default, anonymous volumes attached to containers will not be removed. You
        can override this with `volumes=True`.

        Any data which is not in a volume will be lost.

        Parameters:
            services: The names of one or more services to remove (str or list of str).
                If `None` (the default) then all services are removed.
                If an empty list is provided, this function call is a no-op.
            stop: Stop the containers, if required, before removing
            volumes: Remove any anonymous volumes attached to containers
        """
        full_cmd = self.docker_compose_cmd + ["rm", "--force"]
        full_cmd.add_flag("--stop", stop)
        full_cmd.add_flag("--volumes", volumes)
        if services == []:
            return
        elif services is not None:
            full_cmd += to_list(services)
        run(full_cmd)

    def run(
        self,
        service: str,
        command: List[str] = [],
        build: bool = False,
        detach: bool = False,
        # entrypoint: Optional[List[str]] = None,
        # envs: Dict[str, str] = {},
        labels: Dict[str, str] = {},
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

        Parameters:
            service: The name of the service.
            command: The command to execute.
            detach: if `True`, returns immediately with the Container.
                    If `False`, returns the command stdout as string.
            labels: Add or override labels
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

        Returns:
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
        full_cmd.add_flag("--build", build)
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
        full_cmd.add_args_list("--label", format_dict_for_cli(labels))
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

    @overload
    def start(
        self,
        services: Union[str, List[str], None] = ...,
        stream_logs: Literal[True] = ...,
    ) -> Iterable[Tuple[str, bytes]]:
        ...

    @overload
    def start(
        self,
        services: Union[str, List[str], None] = ...,
        stream_logs: Literal[False] = ...,
    ) -> None:
        ...

    def start(
        self, services: Union[str, List[str], None] = None, stream_logs: bool = False
    ):
        """Start the specified services.

        Parameters:
            services: The names of one or more services to start.
                If `None` (the default), it means all services will start.
                If an empty list is provided, this function call is a no-op.
            stream_logs: If `False` this function returns None. If `True`, this
                function returns an Iterable of `Tuple[str, bytes]` where the first element
                is the type of log (`"stdin"` or `"stdout"`). The second element is the log itself,
                as bytes, you'll need to call `.decode()` if you want the logs as `str`.
                See [the streaming guide](https://gabrieldemarmiesse.github.io/python-on-whales/user_guide/docker_run/#stream-the-output) if you are
                not familiar with the streaming of logs in Python-on-whales.
        """
        full_cmd = self.docker_compose_cmd + ["start"]
        if services == []:
            return
        elif services is not None:
            full_cmd += to_list(services)
        if stream_logs:
            return stream_stdout_and_stderr(full_cmd)
        else:
            run(full_cmd)

    @overload
    def stop(
        self,
        services: Union[str, List[str], None] = ...,
        timeout: Union[int, timedelta, None] = ...,
        stream_logs: Literal[True] = ...,
    ) -> Iterable[Tuple[str, bytes]]:
        ...

    @overload
    def stop(
        self,
        services: Union[str, List[str], None] = ...,
        timeout: Union[int, timedelta, None] = ...,
        stream_logs: Literal[False] = ...,
    ) -> None:
        ...

    def stop(
        self,
        services: Union[str, List[str], None] = None,
        timeout: Union[int, timedelta, None] = None,
        stream_logs: bool = False,
    ):
        """Stop services

        Parameters:
            services: The names of one or more services to stop (str or list of str).
                If `None` (the default), it means all services will stop.
                If an empty list is provided, this function call is a no-op.
            timeout: Number of seconds or timedelta (will be converted to seconds).
                Specify a shutdown timeout. Default is 10s.
            stream_logs: If `False` this function returns None. If `True`, this
                function returns an Iterable of `Tuple[str, bytes]` where the first element
                is the type of log (`"stdin"` or `"stdout"`). The second element is the log itself,
                as bytes, you'll need to call `.decode()` if you want the logs as `str`.
                See [the streaming guide](https://gabrieldemarmiesse.github.io/python-on-whales/user_guide/docker_run/#stream-the-output) if you are
                not familiar with the streaming of logs in Python-on-whales.
        """
        if isinstance(timeout, timedelta):
            timeout = int(timeout.total_seconds())

        full_cmd = self.docker_compose_cmd + ["stop"]
        full_cmd.add_simple_arg("--timeout", timeout)
        if services == []:
            return
        elif services is not None:
            full_cmd += to_list(services)
        if stream_logs:
            return stream_stdout_and_stderr(full_cmd)
        else:
            run(full_cmd)

    def top(self):
        """Not yet implemented"""
        raise NotImplementedError

    def unpause(self, services: Union[str, List[str], None] = None):
        """Unpause one or more services

        Parameters:
            services: One or more service to unpause.
                If `None` (the default), all services are unpaused.
                If services is an empty list, the function call does nothing,
                it's a no-op.
        """
        full_cmd = self.docker_compose_cmd + ["unpause"]
        if services == []:
            return
        elif services is not None:
            full_cmd += to_list(services)
        run(full_cmd)

    @overload
    def up(
        self,
        services: Union[List[str], str, None] = ...,
        build: bool = ...,
        detach: bool = ...,
        abort_on_container_exit: bool = ...,
        scales: Dict[str, int] = ...,
        attach_dependencies: bool = ...,
        force_recreate: bool = ...,
        recreate: bool = ...,
        no_build: bool = ...,
        remove_orphans: bool = ...,
        renew_anon_volumes: bool = ...,
        color: bool = ...,
        log_prefix: bool = ...,
        start: bool = ...,
        quiet: bool = ...,
        wait: bool = ...,
        no_attach_services: Union[List[str], str, None] = ...,
        pull: Literal["always", "missing", "never", None] = ...,
        stream_logs: Literal[True] = ...,
    ) -> Iterable[Tuple[str, bytes]]:
        ...

    @overload
    def up(
        self,
        services: Union[List[str], str, None] = ...,
        build: bool = ...,
        detach: bool = ...,
        abort_on_container_exit: bool = ...,
        scales: Dict[str, int] = ...,
        attach_dependencies: bool = ...,
        force_recreate: bool = ...,
        recreate: bool = ...,
        no_build: bool = ...,
        remove_orphans: bool = ...,
        renew_anon_volumes: bool = ...,
        color: bool = ...,
        log_prefix: bool = ...,
        start: bool = ...,
        quiet: bool = ...,
        wait: bool = ...,
        no_attach_services: Union[List[str], str, None] = ...,
        pull: Literal["always", "missing", "never", None] = ...,
        stream_logs: Literal[False] = ...,
    ) -> None:
        ...

    def up(
        self,
        services: Union[List[str], str, None] = None,
        build: bool = False,
        detach: bool = False,
        abort_on_container_exit: bool = False,
        scales: Dict[str, int] = {},
        attach_dependencies: bool = False,
        force_recreate: bool = False,
        recreate: bool = True,
        no_build: bool = False,
        remove_orphans: bool = False,
        renew_anon_volumes: bool = False,
        color: bool = True,
        log_prefix: bool = True,
        start: bool = True,
        quiet: bool = False,
        wait: bool = False,
        no_attach_services: Union[List[str], str, None] = None,
        pull: Literal["always", "missing", "never", None] = None,
        stream_logs: bool = False,
    ):
        """Start the containers.

        Reading the logs of the containers is not yet implemented.

        Parameters:
            services: The services to start. If `None` (default), all services are
                started. If an empty list is provided, the function call does nothing, it's
                a no-op.
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
            recreate: Recreate the containers if already exist.
                `recreate=False` and `force_recreate=True` are incompatible.
            no_build: Don't build an image, even if it's missing.
            remove_orphans: Remove containers for services not defined in the Compose file.
            renew_anon_volumes: Recreate anonymous volumes instead of retrieving
                data from the previous containers.
            color: If `False`, it will produce monochrome output.
            log_prefix: If `False`, will not display the prefix in the logs.
            start: Start the service after creating them.
            quiet: By default, some progress bars and logs are sent to stderr and stdout.
                Set `quiet=True` to avoid having any output.
            wait: Wait for services to be running|healthy. Implies detached mode.
            no_attach_services: The services not to attach to.
            pull: Pull image before running (“always”|”missing”|”never”).
            stream_logs: If `False` this function returns None. If `True`, this
                function returns an Iterable of `Tuple[str, bytes]` where the first element
                is the type of log (`"stdin"` or `"stdout"`). The second element is the log itself,
                as bytes, you'll need to call `.decode()` if you want the logs as `str`.
                See [the streaming guide](https://gabrieldemarmiesse.github.io/python-on-whales/user_guide/docker_run/#stream-the-output) if you are
                not familiar with the streaming of logs in Python-on-whales.
        """
        if quiet and stream_logs:
            raise ValueError(
                "It's not possible to have stream_logs=True and quiet=True at the same time. "
                "Only one can be activated at a time."
            )
        full_cmd = self.docker_compose_cmd + ["up"]
        full_cmd.add_flag("--build", build)
        full_cmd.add_flag("--detach", detach)
        full_cmd.add_flag("--wait", wait)
        full_cmd.add_flag("--abort-on-container-exit", abort_on_container_exit)
        for service, scale in scales.items():
            full_cmd.add_simple_arg("--scale", f"{service}={scale}")
        full_cmd.add_flag("--attach-dependencies", attach_dependencies)
        full_cmd.add_flag("--force-recreate", force_recreate)
        full_cmd.add_flag("--no-recreate", not recreate)
        full_cmd.add_flag("--no-build", no_build)
        full_cmd.add_flag("--no-color", not color)
        full_cmd.add_flag("--no-log-prefix", not log_prefix)
        full_cmd.add_flag("--no-start", not start)
        full_cmd.add_flag("--remove-orphans", remove_orphans)
        full_cmd.add_flag("--renew-anon-volumes", renew_anon_volumes)
        full_cmd.add_simple_arg("--pull", pull)

        if no_attach_services is not None:
            no_attach_services = to_list(no_attach_services)
            for service in no_attach_services:
                full_cmd.add_simple_arg("--no-attach", service)

        if services == []:
            return
        elif services is not None:
            services = to_list(services)
            full_cmd += services

        if stream_logs:
            return stream_stdout_and_stderr(full_cmd)
        else:
            # important information is written to both stdout AND stderr.
            run(full_cmd, capture_stdout=quiet, capture_stderr=quiet)

    def version(self) -> str:
        """Returns the version of docker compose as a `str`."""
        return run(self.docker_compose_cmd + ["version"])

    def is_installed(self) -> bool:
        """Returns `True` if docker compose (the one written in Go)
        is installed and working."""
        full_cmd = self.docker_cmd + ["compose", "--help"]
        help_output = run(full_cmd)
        return "compose" in help_output
