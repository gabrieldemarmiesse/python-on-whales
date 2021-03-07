from datetime import datetime
from typing import Any, Dict, List, Optional

import python_on_whales.components.container.models
from python_on_whales.utils import DockerCamelModel


class ImageHealthcheck(DockerCamelModel):
    test: List[str]
    interval: int
    timeout: int
    retries: int
    start_period: int


class ImageGraphDriver(DockerCamelModel):
    name: str
    data: Any


class ImageRootFS(DockerCamelModel):
    type: str
    layers: List[str]
    base_layer: Optional[str]


class ImageInspectResult(DockerCamelModel):
    id: str
    repo_tags: List[str]
    repo_digests: List[str]
    parent: str
    comment: str
    created: datetime
    container: str
    container_config: python_on_whales.components.container.models.ContainerConfig
    docker_version: str
    author: str
    config: python_on_whales.components.container.models.ContainerConfig
    architecture: str
    os: str
    os_version: Optional[str]
    size: int
    virtual_size: int
    graph_driver: ImageGraphDriver
    root_fs: ImageRootFS
    metadata: Optional[Dict[str, str]]
