import base64
import json
import warnings
from typing import Dict, List, Literal, Optional

import pydantic
from typing_extensions import Annotated

from python_on_whales.client_config import ClientConfig, DockerCLICaller
from python_on_whales.components.buildx.cli_wrapper import BuildxCLI
from python_on_whales.components.compose.cli_wrapper import ComposeCLI
from python_on_whales.components.config.cli_wrapper import ConfigCLI
from python_on_whales.components.container.cli_wrapper import ContainerCLI
from python_on_whales.components.context.cli_wrapper import ContextCLI
from python_on_whales.components.image.cli_wrapper import ImageCLI
from python_on_whales.components.manifest.cli_wrapper import ManifestCLI
from python_on_whales.components.network.cli_wrapper import NetworkCLI
from python_on_whales.components.node.cli_wrapper import NodeCLI
from python_on_whales.components.plugin.cli_wrapper import PluginCLI
from python_on_whales.components.pod.cli_wrapper import PodCLI
from python_on_whales.components.secret.cli_wrapper import SecretCLI
from python_on_whales.components.service.cli_wrapper import ServiceCLI
from python_on_whales.components.stack.cli_wrapper import StackCLI
from python_on_whales.components.swarm.cli_wrapper import SwarmCLI
from python_on_whales.components.system.cli_wrapper import SystemCLI
from python_on_whales.components.task.cli_wrapper import TaskCLI
from python_on_whales.components.trust.cli_wrapper import TrustCLI
from python_on_whales.components.volume.cli_wrapper import VolumeCLI

from .utils import DockerCamelModel, ValidPath, run


class ClientVersion(DockerCamelModel):
    platform: Optional[Dict[str, str]] = None
    version: Optional[str] = None
    api_version: Annotated[
        Optional[str],
        pydantic.Field(
            validation_alias=pydantic.AliasChoices("APIVersion", "ApiVersion")
        ),
    ] = None
    default_api_version: Optional[str] = None
    git_commit: Optional[str] = None
    go_version: Optional[str] = None
    os: Optional[str] = None
    arch: Optional[str] = None
    build_time: Annotated[
        Optional[str],
        pydantic.Field(
            validation_alias=pydantic.AliasChoices("BuildTime", "BuiltTime")
        ),
    ] = None
    context: Optional[str] = None
    experimental: Optional[bool] = None


class ServerVersionComponent(DockerCamelModel):
    name: Optional[str] = None
    version: Optional[str] = None
    details: Optional[Dict[str, str]] = None


class ServerVersion(DockerCamelModel):
    platform: Optional[Dict[str, str]] = None
    components: Optional[List[ServerVersionComponent]] = None
    version: Optional[str] = None
    api_version: Annotated[
        Optional[str],
        pydantic.Field(
            validation_alias=pydantic.AliasChoices("APIVersion", "ApiVersion")
        ),
    ] = None
    min_api_version: Optional[str] = None
    git_commit: Optional[str] = None
    go_version: Optional[str] = None
    os: Optional[str] = None
    arch: Optional[str] = None
    kernel_version: Optional[str] = None
    build_time: Annotated[
        Optional[str],
        pydantic.Field(
            validation_alias=pydantic.AliasChoices("BuildTime", "BuiltTime")
        ),
    ] = None


class Version(DockerCamelModel):
    client: Optional[ClientVersion] = None
    server: Optional[ServerVersion] = None


class DockerClient(DockerCLICaller):
    """Creates a Docker client

    Note that
    ```python
    from python_on_whales import docker
    print(docker.run("hello-world"))
    ```
    is equivalent to
    ```python
    from python_on_whales import DockerClient
    docker = DockerClient()
    print(docker.run("hello-world")
    ```

    Parameters:
        config: Location of client config files (default "~/.docker")
        context: Name of the context to use to connect to the
            daemon (overrides DOCKER_HOST env var
            and default context set with "docker context use")
        debug: Enable debug mode
        host: Daemon socket(s) to connect to
        log_level: Set the logging level ("debug"|"info"|"warn"|"error"|"fatal")
            (default "info")
        tls:  Use TLS; implied by `tlsverify`
        tlscacert: Trust certs signed only by this CA (default "~/.docker/ca.pem")
        compose_files: Docker compose yaml file
        compose_profiles: List of compose profiles to use. Take a look at
            the [documentation for profiles](https://docs.docker.com/compose/profiles/).
        compose_env_file: .env file containing the environments variables to inject
            into the compose project. By default, it uses `./.env`.
        compose_project_name: The name of the compose project. It will be prefixed to
            networks, volumes and containers created by compose.
        compose_project_directory: Use an alternate working directory. By default, it
            uses the path of the compose file.
        compose_compatibility: Use docker compose in compatibility mode.
        client_call: Client binary to use and how to call it. Default is `["docker"]`. You can try with
            for example `["podman"]` or `["nerdctl"]`. The client must have the same commands and
            outputs as Docker to work. Some best effort support is done in case of divergences,
            meaning you can report issues occuring on some other binary than Docker, but
            we don't guarantee that it will be fixed.
            This option is a list because you can provide a list of command line arguments to be placed after `"docker"`.
            For exemple `host="ssh://my_user@host.com"` is equivalent
            to `client_call=["docker", "--host=ssh://my_user@host.com"]`.
            This will allow you to use some exotic options that are not explicitly supported by Python-on-whales.
            Let's say you want to use estargz to run a container immediately, without waiting for the "pull"
            to finish (yes it's possible!), you can
            do `nerdctl = DockerClient(client_call=["nerdctl", "--snapshotter=stargz"])`
            and then `nerdctl.run("ghcr.io/stargz-containers/python:3.7-org", ["-c", "print('hi')"])`.
            You can also use this system to call Docker with sudo with `client_call=["sudo", "docker"]`
            (note that it won't ask for your password, so sudo should be passwordless during the python
            program execution).
        client_binary: Deprecated, use `client_call`. If you used before `client_binary="podman"`, now use
            `client_call=["podman"]`.
        client_type: The kind of client that is called by the Python process. It allows Python-on-whales to
            adapt to the client's behavior if two client have a different behavior. The `client_call` is not
            enough for Python-on-whales to know what kind of client you're using. For example, if you use
            a symlink to call Docker, Python-on-whales will not know that you're using Docker.
            Default is "unknown". If at some point, Python-on-whales has to choose
            a behavior and `client_type` is `"unknown"`, it will raise an exception and ask you to specify
            what kind of client you're working with. Valid values are `"docker"`, `"podman"`, "`nerdctl"` and `"unknown"`.
    """

    def __init__(
        self,
        config: Optional[ValidPath] = None,
        context: Optional[str] = None,
        debug: Optional[bool] = None,
        host: Optional[str] = None,
        log_level: Optional[str] = None,
        tls: Optional[bool] = None,
        tlscacert: Optional[ValidPath] = None,
        tlscert: Optional[ValidPath] = None,
        tlskey: Optional[ValidPath] = None,
        tlsverify: Optional[bool] = None,
        client_config: Optional[ClientConfig] = None,
        compose_files: List[ValidPath] = [],
        compose_profiles: List[str] = [],
        compose_env_file: Optional[ValidPath] = None,
        compose_env_files: List[ValidPath] = [],
        compose_project_name: Optional[str] = None,
        compose_project_directory: Optional[ValidPath] = None,
        compose_compatibility: Optional[bool] = None,
        client_binary: str = "docker",
        client_call: List[str] = ["docker"],
        client_type: Literal["docker", "podman", "nerdctl", "unknown"] = "unknown",
    ):
        if client_binary != "docker":
            warnings.warn(
                "The usage of client_binary is deprecated, use `client_call` instead. For "
                "example if you used `client_binary='podman'`, now you should use `client_call=['podman']`."
            )
            client_call = [client_binary]

        if client_config is None:
            client_config = ClientConfig(
                config=config,
                context=context,
                debug=debug,
                host=host,
                log_level=log_level,
                tls=tls,
                tlscacert=tlscacert,
                tlscert=tlscert,
                tlskey=tlskey,
                tlsverify=tlsverify,
                compose_files=compose_files,
                compose_profiles=compose_profiles,
                compose_env_file=compose_env_file,
                compose_env_files=compose_env_files,
                compose_project_name=compose_project_name,
                compose_project_directory=compose_project_directory,
                compose_compatibility=compose_compatibility,
                client_call=client_call,
                client_type=client_type,
            )
        super().__init__(client_config)

        self.buildx = BuildxCLI(self.client_config)
        self.compose = ComposeCLI(self.client_config)
        self.config = ConfigCLI(self.client_config)
        self.container = ContainerCLI(self.client_config)
        self.context = ContextCLI(self.client_config)
        self.image = ImageCLI(self.client_config)
        self.manifest = ManifestCLI(self.client_config)
        self.network = NetworkCLI(self.client_config)
        self.node = NodeCLI(self.client_config)
        self.plugin = PluginCLI(self.client_config)
        self.pod = PodCLI(self.client_config)
        self.secret = SecretCLI(self.client_config)
        self.service = ServiceCLI(self.client_config)
        self.stack = StackCLI(self.client_config)
        self.swarm = SwarmCLI(self.client_config)
        self.system = SystemCLI(self.client_config)
        self.task = TaskCLI(self.client_config)
        self.trust = TrustCLI(self.client_config)
        self.volume = VolumeCLI(self.client_config)

        # aliases
        self.attach = self.container.attach
        self.build = self.buildx.build
        self.legacy_build = self.image.legacy_build
        self.commit = self.container.commit
        self.copy = self.container.copy
        self.create = self.container.create
        self.diff = self.container.diff
        self.events = None
        self.execute = self.container.execute
        self.export = self.container.export
        self.images = self.image.list
        self.import_ = self.image.import_
        self.info = self.system.info
        # self.inspect -> too hard to implement
        self.kill = self.container.kill
        self.load = self.image.load
        self.logs = self.container.logs
        self.pause = self.container.pause
        self.ps = self.container.list
        self.pull = self.image.pull
        self.push = self.image.push
        self.rename = self.container.rename
        self.restart = self.container.restart
        self.remove = self.container.remove
        # self.rmi -> doesn't make much sense since it would be docker.remove_image
        self.run = self.container.run
        self.save = self.image.save
        # self.search -> Is anybody going to use it in python?
        self.start = self.container.start
        self.stats = self.container.stats
        self.stop = self.container.stop
        self.tag = self.image.tag
        self.top = self.container.stop
        self.unpause = self.container.unpause
        self.update = self.container.update
        self.wait = self.container.wait

    def version(self) -> Version:
        """
        Get version information about the container client and server.

        # Returns
            A `python_on_whales.Version` object

        As an example:

        ```python
        from python_on_whales import docker

        version_info = docker.version()
        print(version_info.client.version)
        # 3.4.2
        print(version_info.server.kernel_version)
        # 5.15.133.1-microsoft-standard-WSL2
        ...
        ```
        """
        full_cmd = self.docker_cmd + ["version", "-f", "{{json .}}"]
        return Version(**json.loads(run(full_cmd)))

    def login(
        self,
        server: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """Log in to a Docker registry.

        If no server is specified, the default is defined by the daemon.

        Parameters:
            server: The server to log into. For example, with a self-hosted registry
                it might be something like `server="192.168.0.10:5000"`
            username: The username
            password: The password
        """
        full_cmd = self.docker_cmd + ["login", "--password-stdin"]

        full_cmd.add_simple_arg("--username", username)
        if server is not None:
            full_cmd.append(server)

        run(
            full_cmd,
            capture_stderr=False,
            capture_stdout=False,
            input=password.encode(),
        )

    def logout(self, server: Optional[str] = None):
        """Logout from a Docker registry

        Parameters:
            server: The server to logout from. For example, with a self-hosted registry
                it might be something like `server="192.168.0.10:5000"`
        """
        full_cmd = self.docker_cmd + ["logout"]

        if server is not None:
            full_cmd.append(server)

        run(full_cmd, capture_stdout=False, capture_stderr=False)

    def login_ecr(
        self,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        region_name: Optional[str] = None,
        registry: Optional[str] = None,
    ):
        """Login to the aws ECR registry. Credentials are taken from the
        environment variables as defined in
        [the aws docs](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-envvars.html).

        If you don't have a profile or your environment variables configured, you can also
        use the function arguments `aws_access_key_id`, `aws_secret_access_key`, `region_name`.

        Behind the scenes, those arguments are passed directly to
        ```python
        botocore.session.get_session().create_client(...)
        ```

        You need botocore to run this function. Use `pip install botocore` to install it.

        The `registry` parameter can be used to override the registry that is guessed from the authorization token
        request's response.
        In other words: If the registry is `None` (the default) then it will be assumed that it's the ECR registry linked to the credentials provided.
        It is especially useful if the aws account you use can access several repositories and you
        need to explicitly define the one you want to use
        """
        import botocore.session

        client = botocore.session.get_session().create_client(
            "ecr",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name,
        )

        response = client.get_authorization_token()["authorizationData"][0]
        credentials = base64.b64decode(response["authorizationToken"]).decode()
        username, password = credentials.split(":")
        if registry is None:
            registry = response["proxyEndpoint"]
        self.login(registry, username, password)
