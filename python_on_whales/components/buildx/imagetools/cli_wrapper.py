import json
from pathlib import Path
from typing import List, Optional, Union

from python_on_whales.client_config import DockerCLICaller
from python_on_whales.utils import run

from .models import Manifest


class ImagetoolsCLI(DockerCLICaller):
    def inspect(self, name: str) -> Manifest:
        """Returns the manifest of a Docker image in a registry without pulling it"""
        full_cmd = self.docker_cmd + ["buildx", "imagetools", "inspect", "--raw", name]
        result = run(full_cmd)
        return Manifest(**json.loads(result))

    def create(
        self,
        sources: List[str] = [],
        tags: List[str] = [],
        append: bool = False,
        files: List[Union[str, Path]] = [],
        dry_run: bool = False,
        builder: Optional[str] = None,
    ) -> Optional[Manifest]:
        """
        Create a new manifest list based on source manifests.
        The source manifests can be manifest lists or single platform distribution manifests and
        must already exist in the registry where the new manifest is created.
        If only one source is specified, create performs a carbon copy.

        The CLI docs is [here](https://docs.docker.com/engine/reference/commandline/buildx_imagetools_create/)
        and it contains a lot more information.

        Parameters:
            sources: The sources manifest to create, change
            append: Append to existing manifest
            dry_run: Show final image instead of pushing
            files: Read source descriptor from file
            builder: The builder to use.
        """
        if not isinstance(sources, list):
            raise TypeError(
                "The argument 'sources' of the function docker.buildx.imagetools.create() must be a list of strings."
            )
        if not isinstance(tags, list):
            raise TypeError(
                "The argument 'tags' of the function docker.buildx.imagetools.create() must be a list of strings."
            )
        if not isinstance(files, list):
            raise TypeError(
                "The argument 'files' of the function docker.buildx.imagetools.create() must be a list of strings."
            )

        full_cmd = self.docker_cmd + ["buildx", "imagetools", "create"]
        for tag in tags:
            full_cmd.add_simple_arg("--tag", tag)
        for file in files:
            full_cmd.add_simple_arg("--file", file)
        full_cmd.add_simple_arg("--builder", builder)
        full_cmd.add_flag("--append", append)
        full_cmd.add_flag("--dry-run", dry_run)
        full_cmd += sources

        result = run(full_cmd)
        if dry_run:
            return Manifest(**json.loads(result))
