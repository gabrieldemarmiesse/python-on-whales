import subprocess
from pathlib import Path
from typing import List, Optional, Tuple, Union

from typeguard import typechecked

from docker_cli_wrapper.components.buildx import BuildxCLI

from .container import ContainerCLI
from .image import ImageCLI
from .utils import ValidPath, run
from .volume import VolumeCLI


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
        self.config = config
        self.context = context
        self.debug = debug
        self.host = host
        self.log_level = log_level
        self.tls = tls
        self.tlscacert = tlscacert
        self.tlscert = tlscert
        self.tlskey = tlskey
        self.tlsverify = tlsverify
        self.version = version

        self.volume = VolumeCLI(self._make_cli_cmd())
        self.image = ImageCLI(self._make_cli_cmd())
        self.container = ContainerCLI(self._make_cli_cmd())
        self.buildx = BuildxCLI(self._make_cli_cmd())

        # aliases
        self.run = self.container.run
        self.pull = self.image.pull
        self.push = self.image.push

    def _make_cli_cmd(self) -> List[str]:
        result = ["docker"]

        if self.config is not None:
            result += ["--config", self.config]

        return result
