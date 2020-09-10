from typing import Optional

from python_on_whales.client_config import ClientConfig, DockerCLICaller
from python_on_whales.components.buildx import BuildxCLI
from python_on_whales.components.container import ContainerCLI
from python_on_whales.components.image import ImageCLI
from python_on_whales.components.network import NetworkCLI
from python_on_whales.components.node import NodeCLI
from python_on_whales.components.service import ServiceCLI
from python_on_whales.components.system import SystemCLI
from python_on_whales.components.volume import VolumeCLI

from .utils import ValidPath, run


class DockerClient(DockerCLICaller):
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
        self.system = SystemCLI(self.client_config)

        # aliases
        self.build = self.buildx.build
        self.commit = self.container.commit
        self.cp = self.container.cp
        self.diff = self.container.diff
        self.exec = self.container.exec
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
        self.rm = self.container.remove
        self.rmi = self.image.remove
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
        full_cmd = self.docker_cmd + ["login"]

        if username is not None:
            full_cmd += ["--username", username]

        if password is not None:
            full_cmd += ["--password", password]

        if server is not None:
            full_cmd.append(password)

        run(full_cmd, capture_stderr=False, capture_stdout=False)

    def logout(self, server: Optional[str] = None):
        full_cmd = self.docker_cmd + ["logout"]

        if server is not None:
            full_cmd.append(server)

        run(full_cmd, capture_stdout=False, capture_stderr=False)
