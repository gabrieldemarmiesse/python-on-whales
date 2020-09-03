import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional

from .utils import ValidPath


@dataclass(frozen=True)
class ClientConfig:

    config: Optional[ValidPath] = None
    context: Optional[str] = None
    debug: Optional[bool] = None
    host: Optional[str] = None
    log_level: Optional[str] = None
    tls: Optional[bool] = None
    tlscacert: Optional[ValidPath] = None
    tlscert: Optional[ValidPath] = None
    tlskey: Optional[ValidPath] = None
    tlsverify: Optional[bool] = None
    version: bool = False

    @property
    def docker_cmd(self) -> List[str]:
        result = ["docker"]

        if self.config is not None:
            result += ["--config", self.config]

        return result


class DockerCLICaller:
    def __init__(self, client_config: ClientConfig):
        self.client_config = client_config

    @property
    def docker_cmd(self) -> List[str]:
        return self.client_config.docker_cmd


class ReloadableObject(DockerCLICaller):
    def __init__(self, client_config: ClientConfig):
        super().__init__(client_config)
        self._last_refreshed_time = datetime.min

    def _needs_reload(self) -> bool:
        return (datetime.now() - self._last_refreshed_time) >= timedelta(seconds=0.2)

    def reload(self, *args, **kwargs):
        self._reload(*args, **kwargs)
        self._last_refreshed_time = datetime.now()

    def _reload(self, *args, **kwargs):
        raise NotImplementedError

    def _reload_if_necessary(self):
        if self._needs_reload():
            self.reload()
