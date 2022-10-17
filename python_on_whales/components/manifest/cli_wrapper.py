from typing import Any, Dict, List, Union

from python_on_whales.client_config import (
    ClientConfig,
    DockerCLICaller,
    ReloadableObjectFromJson
)
from python_on_whales.components.manifest.models import ManifestListInspectResult
from python_on_whales.components.buildx.imagetools.models import ImageVariantManifest
from python_on_whales.utils import run, to_list

class ManifestList(ReloadableObjectFromJson):
    def __init__(
        self, client_config: ClientConfig, reference: str, is_immutable_id=False
    ):
        super().__init__(client_config, "id", reference, is_immutable_id)
    
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.remove()

    def _fetch_inspect_result_json(self, reference):
        return run(self.docker_cmd + ["manifest", "inspect", reference])

    def _parse_json_object(self, json_object: Dict[str, Any]) -> ManifestListInspectResult:
        return ManifestListInspectResult.parse_obj(json_object)

    def _get_inspect_result(self) -> ManifestListInspectResult:
        """Only there to allow tools to know the return type"""
        return super()._get_inspect_result()

    @property
    def id(self) -> str:
        return self._get_immutable_id()

    @property
    def name(reference) -> str:
        return reference

    @property
    def schema_version(self) -> str:
        return self._get_inspect_result().schema_version

    @property
    def media_type(self) -> str:
        return self._get_inspect_result().media_type

    @property
    def manifests(self) -> List[ImageVariantManifest]:
        return self._get_inspect_result().manifests

    def __repr__(self):
        return f"python_on_whales.ManifestList(name='{self.name}')"

    def remove(self) -> None:
        """Removes this Docker manifest list.

        Rather than removing it manually, you can use a context manager to
        make sure the manifest list is deleted even if an exception is raised.
        """
        ManifestCLI(self.client_config).remove(self)

ValidManifestList = Union[ManifestList, str]

class ManifestCLI(DockerCLICaller):
    def annotate(
        self,
        name: str,
        manifest: str,
        arch: str = None,
        os: str = None,
        os_features: List[str] = None,
        os_version: str = None,
        variant: str = None,
    ) -> ManifestList:
        """Annotates a Docker manifest list.

        # Arguments
            name: The name of the manifest list
            manifest: The individual manifest to annotate
            arch: The manifest's architecture
            os: The manifest's operating system
            os_features: The manifest's operating system features
            os_version: The manifest's operating system version
            variant: The manifest's architecture variant
        """
        full_cmd = self.docker_cmd + ["manifest", "annotate"]
        full_cmd.add_simple_arg("--arch", arch)
        full_cmd.add_simple_arg("--os", os)
        full_cmd.add_simple_arg("--os-features", os_features)
        full_cmd.add_simple_arg("--os-version", os_version)
        full_cmd.add_simple_arg("--variant", variant)
        full_cmd.append(name)
        full_cmd.append(manifest)
        run(full_cmd)

    def create(
        self,
        name: str,
        manifests: List[str],
        ammend: bool = False,
        insecure: bool = False,
    ) -> ManifestList:
        """Creates a Docker manifest list.

        # Arguments
            name: The name of the manifest list
            manifests: The list of manifests to add to the manifest list
        
        # Returns
            A `python_on_whales.ManifestList`.
        """
        full_cmd = self.docker_cmd + ["manifest", "create"]
        full_cmd.add_flag("--amend", ammend)
        full_cmd.add_flag("--insecure", insecure)
        full_cmd.append(name)
        full_cmd += to_list(manifests)
        return ManifestList(self.client_config, run(full_cmd), is_immutable_id=True)

    def inspect(self, x: str) -> ManifestList:
        """Returns a Docker manifest list object.
        """
        return ManifestList(self.client_config, x)


    def push(self):
        """Not yet implemented"""
        raise NotImplementedError

    def remove(self, manifest_lists: Union[ValidManifestList, List[ValidManifestList]]):
        """Removes a Docker manifest list.

        # Arguments
            manifest_lists: One or more manifest lists.
        """
        if manifest_lists == []:
            return
        full_cmd = self.docker_cmd + ["manifest", "rm"]
        full_cmd += to_list(manifest_lists)
        run(full_cmd)
