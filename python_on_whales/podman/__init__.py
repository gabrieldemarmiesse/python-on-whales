"""
Podman-specific entrypoints for python-on-whales.

This subpackage exists to create a python_on_whales.podman namespace:

from python_on_whales.podman import podman, PodmanClient, PodmanImage
```
"""

from ..components.system.cli_wrapper import PodmanSystemInfo
from .podman_client import PodmanClient

# Common entrypoint, mirroring python_on_whales.docker to have python_on_whales.podman.podman
podman = PodmanClient()

__all__ = [
    "PodmanClient",
    "PodmanSystemInfo",
    "podman",
]
