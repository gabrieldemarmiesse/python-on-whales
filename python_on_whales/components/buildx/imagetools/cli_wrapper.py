from python_on_whales.client_config import DockerCLICaller
from python_on_whales.utils import run

from .models import Manifest


class ImagetoolsCLI(DockerCLICaller):
    def inspect(self, name: str) -> Manifest:
        """Returns the manifest of a Docker image in a registry without pulling it"""
        full_cmd = self.docker_cmd + ["buildx", "imagetools", "inspect", "--raw", name]
        result = run(full_cmd)
        return Manifest.parse_raw(result)
