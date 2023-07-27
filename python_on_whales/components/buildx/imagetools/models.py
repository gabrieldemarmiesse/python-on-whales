from __future__ import annotations

from typing import List, Optional

import pydantic
from typing_extensions import Annotated


class ManifestConfig(pydantic.BaseModel):
    media_type: Annotated[Optional[str], pydantic.Field(alias="mediaType")] = None
    digest: Optional[str] = None
    size: Optional[int] = None


class ManifestLayer(pydantic.BaseModel):
    media_type: Annotated[Optional[str], pydantic.Field(alias="mediaType")] = None
    digest: Optional[str] = None
    size: Optional[int] = None


class ManifestPlatform(pydantic.BaseModel):
    architecture: Optional[str] = None
    os: Optional[str] = None
    os_version: Optional[str] = None
    variant: Optional[str] = None


class ImageVariantManifest(pydantic.BaseModel):
    media_type: Annotated[Optional[str], pydantic.Field(alias="mediaType")] = None
    size: Optional[int] = None
    digest: Optional[str] = None
    platform: Optional[ManifestPlatform] = None


class Manifest(pydantic.BaseModel):
    media_type: Annotated[Optional[str], pydantic.Field(alias="mediaType")]
    schema_version: Annotated[Optional[int], pydantic.Field(alias="schemaVersion")]
    layers: Optional[List[ManifestLayer]] = None
    manifests: Optional[List[ImageVariantManifest]] = None
    config: Optional[ManifestConfig] = None
