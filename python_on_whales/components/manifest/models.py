from typing import List, Optional

from python_on_whales.components.buildx.imagetools.models import ImageVariantManifest
from python_on_whales.utils import DockerCamelModel


class ManifestListInspectResult(DockerCamelModel):
    name: Optional[str] = None
    schema_version: Optional[int] = None
    media_type: Optional[str] = None
    manifests: Optional[List[ImageVariantManifest]] = None
