from typing import List, Optional

from python_on_whales.components.buildx.imagetools.models import ImageVariantManifest
from python_on_whales.utils import DockerCamelModel, all_fields_optional


@all_fields_optional
class ManifestListInspectResult(DockerCamelModel):
    name: Optional[str]
    schema_version: Optional[int]
    media_type: Optional[str]
    manifests: Optional[List[ImageVariantManifest]]
