from __future__ import annotations

from typing import Any, Dict, List, Optional, Union, overload

from python_on_whales.client_config import (
    ClientConfig,
    DockerCLICaller,
    ReloadableObjectFromJson,
)
from python_on_whales.utils import DockerCamelModel, ValidPath, run, to_list


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


class Plugin(ReloadableObjectFromJson):
    def __init__(
        self, client_config: ClientConfig, reference: str, is_immutable_id=False
    ):
        super().__init__(client_config, "id", reference, is_immutable_id)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.remove(force=True)

    def _fetch_inspect_result_json(self, reference):
        return run(self.docker_cmd + ["plugin", "inspect", reference])

    def _parse_json_object(self, json_object: Dict[str, Any]) -> PluginInspectResult:
        return PluginInspectResult.parse_obj(json_object)

    def _get_inspect_result(self) -> PluginInspectResult:
        """Only there to allow tools to know the return type"""
        return super()._get_inspect_result()

    @property
    def id(self) -> str:
        return self._get_immutable_id()

    @property
    def name(self) -> str:
        return self._get_inspect_result().name

    @property
    def enabled(self) -> bool:
        return self._get_inspect_result().enabled

    @property
    def settings(self) -> PluginSettings:
        return self._get_inspect_result().settings

    @property
    def plugin_reference(self) -> str:
        return self._get_inspect_result().plugin_reference

    @property
    def config(self) -> PluginConfig:
        return self._get_inspect_result().config

    @property
    def _docker_plugin(self) -> PluginCLI:
        return PluginCLI(self.client_config)

    def disable(self, force: bool = False) -> None:
        """Disable this plugin"""
        self._docker_plugin.disable(self, force=force)

    def enable(self, timeout: int = None) -> None:
        """Enable this plugin"""
        self._docker_plugin.enable(self, timeout=timeout)

    def push(self, disable_content_trust: bool = True) -> None:
        """Push this plugin"""
        self._docker_plugin.push(self, disable_content_trust=disable_content_trust)

    def remove(self, force: bool = False) -> None:
        """Remove this plugin"""
        self._docker_plugin.remove(self, force=force)

    def set(self, configuration: Dict[str, str]) -> None:
        """Set the configuration for this plugin"""
        self._docker_plugin.set(self, configuration)

    def upgrade(
        self,
        remote: Optional[str] = None,
        disable_content_trust: bool = True,
        skip_remote_check: bool = False,
    ) -> None:
        """Upgrade this plugin"""
        self._docker_plugin.upgrade(
            self, remote, disable_content_trust, skip_remote_check
        )


ValidPlugin = Union[Plugin, str]


class PluginCLI(DockerCLICaller):
    def create(
        self, plugin_name: str, plugin_data_directory: ValidPath, compress: bool = False
    ) -> Plugin:
        """Create a plugin from a rootfs and configuration.

        # Arguments
            plugin_name: The name you want to give to your plugin
            plugin_data_directory: Must contain config.json and rootfs directory.
            compress: Compress the context using gzip
        """
        full_cmd = self.docker_cmd + ["plugin", "create"]
        full_cmd.add_flag("--compress", compress)
        full_cmd += [plugin_name, plugin_data_directory]
        run(full_cmd)
        return Plugin(self.client_config, plugin_name)

    def disable(self, plugin: ValidPlugin, force: bool = False) -> None:
        """Disable a plugin

        # Arguments
            plugin: The plugin to disable
            force: Force the disable of an active plugin
        """
        full_cmd = self.docker_cmd + ["plugin", "disable"]
        full_cmd.add_flag("--force", force)
        full_cmd.append(plugin)
        run(full_cmd)

    def enable(self, plugin: ValidPlugin, timeout: int = None) -> None:
        """Enable a plugin

        # Arguments
            plugin: The plugin to enable
            timeout: HTTP client timeout (in seconds) (default 30)
        """
        full_cmd = self.docker_cmd + ["plugin", "enable"]
        full_cmd.add_simple_arg("--timeout", timeout)
        full_cmd.append(plugin)
        run(full_cmd)

    @overload
    def inspect(self, x: str) -> Plugin:
        ...

    @overload
    def inspect(self, x: List[str]) -> List[Plugin]:
        ...

    def inspect(self, x: Union[str, List[str]]) -> Union[Plugin, List[Plugin]]:
        """Returns a `python_on_whales.Plugin` object from a string
        (name or id of the plugin)

        # Arguments
            x: One id or hostname or a list of name or ids

        # Returns
            One or a list of `python_on_whales.Plugin`
        """
        if isinstance(x, str):
            return Plugin(self.client_config, x)
        else:
            return [Plugin(self.client_config, reference) for reference in x]

    def install(
        self,
        plugin_name: str,
        configuration: Dict[str, str] = {},
        alias: Optional[str] = None,
        disable: bool = False,
        disable_content_trust: bool = True,
    ) -> Plugin:
        """Installs a Docker plugin

        Warning: `--grant-all-permissions` is enabled, which means the program won't
        stop to ask you to grant the permissions.

        # Arguments
            plugin_name: The name of the plugin you want to install
            configuration: A `dict` adding configuration options to the plugin
            alias: Local name for plugin
            disable: Do not enable the plugin on install
            disable_content_trust: Skip image verification (default `True`)

        # Returns
            A `python_on_whales.Plugin`.
        """
        full_cmd = self.docker_cmd + ["plugin", "install", "--grant-all-permissions"]
        full_cmd.add_simple_arg("--alias", alias)
        full_cmd.add_flag("--disable", disable)
        if not disable_content_trust:
            full_cmd.append("--disable-content-trust=false")
        full_cmd.append(plugin_name)
        for key, value in configuration.items():
            full_cmd.append(f"{key}={value}")
        run(full_cmd)
        if alias is not None:
            return Plugin(self.client_config, alias)
        return Plugin(self.client_config, plugin_name)

    def list(self) -> List[Plugin]:
        """Returns a `List[python_on_whales.Plugin` that are installed on the daemon."""
        full_cmd = self.docker_cmd + [
            "docker",
            "plugin",
            "list",
            "--no-trunc",
            "--quiet",
        ]
        ids = run(full_cmd).splitlines()
        return [Plugin(self.client_config, id_, is_immutable_id=True) for id_ in ids]

    def push(self, plugin: ValidPlugin, disable_content_trust: bool = True) -> None:
        """Push a plugin to a registry.


        # Arguments
            plugin: The plugin to push
            disable_content_trust: Skip image signing (default `True`)
        """
        full_cmd = self.docker_cmd + ["plugin", "push"]
        if not disable_content_trust:
            full_cmd.append("--disable-content-trust=false")
        full_cmd.append(plugin)
        run(full_cmd)

    def remove(
        self, x: Union[ValidPlugin, List[ValidPlugin]], force: bool = False
    ) -> None:
        """Removes one or more plugins

        # Arguments
            plugin: One or more plugins to remove.
            force: Force the removal of this plugin.
        """
        full_cmd = self.docker_cmd + ["plugin", "remove"]
        full_cmd.add_flag("--force", force)
        full_cmd += to_list(x)
        run(full_cmd)

    def set(self, plugin: ValidPlugin, configuration: Dict[str, str]) -> None:
        """Change the settings for a plugin

        # Arguments
            plugin: The plugin that needs its settings changed
            configuration: The new configuration options.
        """
        full_cmd = self.docker_cmd + ["plugin", "set"]
        full_cmd.append(plugin)
        for key, value in configuration.items():
            full_cmd.append(f"{key}={value}")
        run(full_cmd)

    def upgrade(
        self,
        plugin: ValidPlugin,
        remote: Optional[str] = None,
        disable_content_trust: bool = True,
        skip_remote_check: bool = False,
    ) -> None:
        """Upgrade a plugin

        Warning: `--grant-all-permissions` is enabled, which means the program won't
        stop to ask you to grant the permissions.

        # Arguments
            plugin: The plugin to upgrade
            remote: The remote to fetch the upgrade from
            disable_content_trust: Skip image verification (default `True`)
            skip_remote_check: Do not check if specified remote plugin matches
                existing plugin image
        """
        full_cmd = self.docker_cmd + ["plugin", "upgrade", "--grant-all-permissions"]
        if not disable_content_trust:
            full_cmd.append("--disable-content-trust=false")
        full_cmd.add_flag("--skip-remote-check", skip_remote_check)
        full_cmd.append(plugin)
        if remote is not None:
            full_cmd.append(remote)
        run(full_cmd)
