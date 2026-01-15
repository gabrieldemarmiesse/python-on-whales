from typing import Union

from ..components.system.cli_wrapper import DockerSystemCLI, PodmanSystemCLI
from ..components.system.models import DockerSystemInfo, PodmanSystemInfo
from ..docker_client import DockerClient
from ..podman import PodmanClient

ContainerEngineClient = Union[DockerClient, PodmanClient]
SystemInfo = Union[DockerSystemInfo, PodmanSystemInfo]
SystemCLI = Union[DockerSystemCLI, PodmanSystemCLI]
