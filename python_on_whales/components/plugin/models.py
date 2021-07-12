from typing import List

from python_on_whales.utils import DockerCamelModel, all_fields_optional


@all_fields_optional
class PluginMount(DockerCamelModel):
    pass


@all_fields_optional
class PluginDevice(DockerCamelModel):
    pass


@all_fields_optional
class PluginSettings(DockerCamelModel):
    mounts: List[PluginMount]
    env: List[str]
    args: List[str]
    devices: List[PluginDevice]


@all_fields_optional
class Interface(DockerCamelModel):
    pass


@all_fields_optional
class PluginConfig(DockerCamelModel):
    docker_version: str
    description: str
    documentation: str
    interface: Interface
    entrypoint: List[str]
    work_dir: str
    # TODO: add missing attributes


@all_fields_optional
class PluginInspectResult(DockerCamelModel):
    id: str
    name: str
    enabled: bool
    settings: PluginSettings
    plugin_reference: str
    config: PluginConfig
