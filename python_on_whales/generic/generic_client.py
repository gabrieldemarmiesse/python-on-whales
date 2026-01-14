from typing import Union

from python_on_whales.docker_client import DockerClient
from python_on_whales.podman import PodmanClient

ContainerEngineClient = Union[DockerClient, PodmanClient]
