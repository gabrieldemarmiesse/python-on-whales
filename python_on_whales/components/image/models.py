from datetime import datetime
from typing import Any, Dict, List, Optional

import python_on_whales.components.container.models
from python_on_whales.utils import DockerCamelModel


class ImageHealthcheck(DockerCamelModel):
    test: Optional[List[str]] = None
    interval: Optional[int] = None
    timeout: Optional[int] = None
    retries: Optional[int] = None
    start_period: Optional[int] = None


class ImageGraphDriver(DockerCamelModel):
    name: Optional[str] = None
    data: Any = None


class ImageRootFS(DockerCamelModel):
    type: Optional[str] = None
    layers: Optional[List[str]] = None
    base_layer: Optional[str] = None


class ImageInspectResult(DockerCamelModel):
    id: Optional[str] = None
    repo_tags: Optional[List[str]] = None
    repo_digests: Optional[List[str]] = None
    parent: Optional[str] = None
    comment: Optional[str] = None
    created: Optional[datetime] = None
    container: Optional[str] = None
    container_config: Optional[
        python_on_whales.components.container.models.ContainerConfig
    ] = None
    docker_version: Optional[str] = None
    author: Optional[str] = None
    config: Optional[python_on_whales.components.container.models.ContainerConfig] = (
        None
    )
    architecture: Optional[str] = None
    os: Optional[str] = None
    os_version: Optional[str] = None
    variant: Optional[str] = None
    size: Optional[int] = None
    virtual_size: Optional[int] = None
    graph_driver: Optional[ImageGraphDriver] = None
    root_fs: Optional[ImageRootFS] = None
    metadata: Optional[Dict[str, str]] = None
