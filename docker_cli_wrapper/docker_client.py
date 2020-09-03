from typing import List, Optional

from docker_cli_wrapper.components.buildx import BuildxCLI
from docker_cli_wrapper.components.container import ContainerCLI
from docker_cli_wrapper.components.image import ImageCLI
from docker_cli_wrapper.components.volume import VolumeCLI
from docker_cli_wrapper.docker_command import DockerCommand

from .utils import ValidPath


class DockerClient:
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
        version: bool = False,
    ):
        self.docker_cmd = DockerCommand(
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

        self.volume = VolumeCLI(self.docker_cmd)
        self.image = ImageCLI(self.docker_cmd)
        self.container = ContainerCLI(self.docker_cmd)
        self.buildx = BuildxCLI(self.docker_cmd)

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
