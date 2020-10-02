from typing import Optional

from python_on_whales.client_config import ClientConfig, DockerCLICaller
from python_on_whales.components.buildx import BuildxCLI
from python_on_whales.components.container import ContainerCLI
from python_on_whales.components.image import ImageCLI
from python_on_whales.components.network import NetworkCLI
from python_on_whales.components.node import NodeCLI
from python_on_whales.components.service import ServiceCLI
from python_on_whales.components.stack import StackCLI
from python_on_whales.components.swarm import SwarmCLI
from python_on_whales.components.system import SystemCLI
from python_on_whales.components.volume import VolumeCLI

from .utils import ValidPath, run


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

    # Arguments
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
    ):

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
            )
        super().__init__(client_config)

        self.volume = VolumeCLI(self.client_config)
        self.image = ImageCLI(self.client_config)
        self.container = ContainerCLI(self.client_config)
        self.buildx = BuildxCLI(self.client_config)
        self.network = NetworkCLI(self.client_config)
        self.service = ServiceCLI(self.client_config)
        self.node = NodeCLI(self.client_config)
        self.stack = StackCLI(self.client_config)
        self.swarm = SwarmCLI(self.client_config)
        self.system = SystemCLI(self.client_config)

        # aliases
        self.build = self.buildx.build
        self.commit = self.container.commit
        self.copy = self.container.copy
        self.create = self.container.create
        self.diff = self.container.diff
        self.execute = self.container.execute
        self.images = self.image.list
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
        self.run = self.container.run
        self.save = self.image.save
        self.stop = self.container.stop
        self.tag = self.image.tag

    def login(
        self,
        server: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """Log in to a Docker registry.

        If no server is specified, the default is defined by the daemon.

        # Arguments
            server: The server to log into. For example, with a self-hosted registry
                it might be something like `server="192.168.0.10:5000"`
            username: The username
            password: The password
        """
        full_cmd = self.docker_cmd + ["login"]

        full_cmd.add_simple_arg("--username", username)
        full_cmd.add_simple_arg("--password", password)
        if server is not None:
            full_cmd.append(server)

        run(full_cmd, capture_stderr=False, capture_stdout=False)

    def logout(self, server: Optional[str] = None):
        """Logout from a Docker registry

        # Arguments
            server: The server to logout from. For example, with a self-hosted registry
                it might be something like `server="192.168.0.10:5000"`
        """
        full_cmd = self.docker_cmd + ["logout"]

        if server is not None:
            full_cmd.append(server)

        run(full_cmd, capture_stdout=False, capture_stderr=False)
