from typing import List

from python_on_whales.components.buildx.imagetools.models import ImageVariantManifest
from python_on_whales.utils import DockerCamelModel, all_fields_optional


@all_fields_optional
class ManifestListInspectResult(DockerCamelModel):
    name: str
    schema_version: int
    media_type: str
    manifests: List[ImageVariantManifest]
