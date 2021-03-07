from typing import List

from python_on_whales.utils import DockerCamelModel


class PluginMount(DockerCamelModel):
    pass


class PluginDevice(DockerCamelModel):
    pass


class PluginSettings(DockerCamelModel):
    mounts: List[PluginMount]
    env: List[str]
    args: List[str]
    devices: List[PluginDevice]


class Interface(DockerCamelModel):
    pass


class PluginConfig(DockerCamelModel):
    docker_version: str
    description: str
    documentation: str
    interface: Interface
    entrypoint: List[str]
    work_dir: str
    # TODO: add missing attributes


class PluginInspectResult(DockerCamelModel):
    id: str
    name: str
    enabled: bool
    settings: PluginSettings
    plugin_reference: str
    config: PluginConfig
