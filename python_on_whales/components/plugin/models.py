from typing import List, Optional

from python_on_whales.utils import DockerCamelModel, all_fields_optional


@all_fields_optional
class PluginMount(DockerCamelModel):
    pass


@all_fields_optional
class PluginDevice(DockerCamelModel):
    pass


@all_fields_optional
class PluginSettings(DockerCamelModel):
    mounts: Optional[List[PluginMount]]
    env: Optional[List[str]]
    args: Optional[List[str]]
    devices: Optional[List[PluginDevice]]


@all_fields_optional
class Interface(DockerCamelModel):
    pass


@all_fields_optional
class PluginConfig(DockerCamelModel):
    docker_version: Optional[str]
    description: Optional[str]
    documentation: Optional[str]
    interface: Optional[Interface]
    entrypoint: Optional[List[str]]
    work_dir: Optional[str]
    # TODO: add missing attributes


@all_fields_optional
class PluginInspectResult(DockerCamelModel):
    id: Optional[str]
    name: Optional[str]
    enabled: Optional[bool]
    settings: Optional[PluginSettings]
    plugin_reference: Optional[str]
    config: Optional[PluginConfig]
