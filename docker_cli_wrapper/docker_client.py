from typing import List, Optional

from docker_cli_wrapper.client_config import ClientConfig, DockerCLICaller
from docker_cli_wrapper.components.buildx import BuildxCLI
from docker_cli_wrapper.components.container import ContainerCLI
from docker_cli_wrapper.components.image import ImageCLI
from docker_cli_wrapper.components.volume import VolumeCLI

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
        version: Optional[bool] = False,
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
                version=version,
            )
        super().__init__(client_config)

        self.volume = VolumeCLI(self.client_config)
        self.image = ImageCLI(self.client_config)
        self.container = ContainerCLI(self.client_config)
        self.buildx = BuildxCLI(self.client_config)

        # aliases
        self.build = self.buildx.build
        self.commit = self.container.commit
        self.cp = self.container.cp
        self.images = self.image.list
        self.kill = self.container.kill
        self.load = self.image.load
        self.logs = self.container.logs
        self.ps = self.container.list
        self.pull = self.image.pull
        self.push = self.image.push
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
