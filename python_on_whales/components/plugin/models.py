from typing import List, Optional

from python_on_whales.utils import DockerCamelModel


class PluginMount(DockerCamelModel):
    pass


class PluginDevice(DockerCamelModel):
    pass


class PluginSettings(DockerCamelModel):
    mounts: Optional[List[PluginMount]] = None
    env: Optional[List[str]] = None
    args: Optional[List[str]] = None
    devices: Optional[List[PluginDevice]] = None


class Interface(DockerCamelModel):
    pass


class PluginConfig(DockerCamelModel):
    docker_version: Optional[str] = None
    description: Optional[str] = None
    documentation: Optional[str] = None
    interface: Optional[Interface] = None
    entrypoint: Optional[List[str]] = None
    work_dir: Optional[str] = None
    # TODO: add missing attributes


class PluginInspectResult(DockerCamelModel):
    id: Optional[str] = None
    name: Optional[str] = None
    enabled: Optional[bool] = None
    settings: Optional[PluginSettings] = None
    plugin_reference: Optional[str] = None
    config: Optional[PluginConfig] = None
