from python_on_whales.components.system.cli_wrapper import PodmanSystemCLI
from python_on_whales.docker_client import _BaseContainerEngineClient


class PodmanClient(_BaseContainerEngineClient):
    """
    Podman client for Podman specific interactions.
    """

    def __init__(self, **kwargs):
        kwargs.setdefault("client_type", "podman")
        super().__init__(**kwargs)
        self.system = PodmanSystemCLI(self.client_config)
        self.info = self.system.info
