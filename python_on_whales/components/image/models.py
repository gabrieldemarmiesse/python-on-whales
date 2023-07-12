from datetime import datetime
from typing import Any, Dict, List, Optional

import python_on_whales.components.container.models
from python_on_whales.utils import DockerCamelModel, all_fields_optional


@all_fields_optional
class ImageHealthcheck(DockerCamelModel):
    test: Optional[List[str]]
    interval: Optional[int]
    timeout: Optional[int]
    retries: Optional[int]
    start_period: Optional[int]


@all_fields_optional
class ImageGraphDriver(DockerCamelModel):
    name: Optional[str]
    data: Any = None


@all_fields_optional
class ImageRootFS(DockerCamelModel):
    type: Optional[str]
    layers: Optional[List[str]]
    base_layer: Optional[str]


@all_fields_optional
class ImageInspectResult(DockerCamelModel):
    id: Optional[str]
    repo_tags: Optional[List[str]]
    repo_digests: Optional[List[str]]
    parent: Optional[str]
    comment: Optional[str]
    created: Optional[datetime]
    container: Optional[str]
    container_config: Optional[
        python_on_whales.components.container.models.ContainerConfig
    ]
    docker_version: Optional[str]
    author: Optional[str]
    config: Optional[python_on_whales.components.container.models.ContainerConfig]
    architecture: Optional[str]
    os: Optional[str]
    os_version: Optional[str]
    size: Optional[int]
    virtual_size: Optional[int]
    graph_driver: Optional[ImageGraphDriver]
    root_fs: Optional[ImageRootFS]
    metadata: Optional[Dict[str, str]]
