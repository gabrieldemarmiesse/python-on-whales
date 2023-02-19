from typing import Any, Dict, Iterator, Optional, Union
import json

from python_on_whales.client_config import DockerCLICaller
from python_on_whales.components.buildx.cli_wrapper import stream_buildx_logs
from python_on_whales.utils import run

from .models import Manifest


class ImagetoolsCLI(DockerCLICaller):
    def inspect(self, name: str) -> Manifest:
        """Returns the manifest of a Docker image in a registry without pulling it"""
        full_cmd = self.docker_cmd + ["buildx", "imagetools", "inspect", "--raw", name]
        result = run(full_cmd)
        return Manifest.parse_raw(result)

    def create(
        self,
        source: str,
        tag: str,
        append: bool = False,
        stream_logs: bool = False,
        file: Optional[str] = None,
        progress: Union[str, bool] = "auto",
        dry_run: Optional[bool] = False,
        builder: Optional[str] = None,
    ) -> Union[Dict[str, Dict[str, Dict[str, Any]]], Iterator[str]]:
        """
        Create a new manifest list based on source manifests.
        The source manifests can be manifest lists or single platform distribution manifests and
        must already exist in the registry where the new manifest is created.
        If only one source is specified, create performs a carbon copy.

        The CLI docs is [here](https://docs.docker.com/engine/reference/commandline/buildx_imagetools_create/)
        and it contains a lot more information.

        # Arguments
            source: The source manifest to create, change
            append: Append to existing manifest
            dry_run: Show final image instead of pushing
            file: Read source descriptor from file
            progress: Set type of progress output (`"auto"`, `"plain"`, `"tty"`,
                or `False`). Use plain to keep the container output on screen
            builder: The builder to use.

        """
        full_cmd = self.docker_cmd + ["buildx", "imagetools", "create"]

        if progress != "auto" and isinstance(progress, str):
            full_cmd += ["--progress", progress]

        full_cmd.add_simple_arg("--tag", tag)
        full_cmd.add_simple_arg("--file", file)
        full_cmd.add_simple_arg("--builder", builder)
        full_cmd.add_flag("--append", append)
        full_cmd.add_flag("--dry_run", dry_run)

        if stream_logs:
            return stream_buildx_logs(full_cmd + source)
        else:
            run(full_cmd)
            return json.loads(run(full_cmd + source))
