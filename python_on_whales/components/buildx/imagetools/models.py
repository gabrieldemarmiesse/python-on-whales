from __future__ import annotations

import pydantic


class ManifestConfig(pydantic.BaseModel):
    media_type: str | None = pydantic.Field(alias="mediaType")
    digest: str | None
    size: int | None


class ManifestLayer(pydantic.BaseModel):
    media_type: str = pydantic.Field(alias="mediaType")
    digest: str | None
    size: int | None


class ManifestPlatform(pydantic.BaseModel):
    architecture: str | None
    os: str | None
    os_version: str | None
    variant: str | None


class ImageVariantManifest(pydantic.BaseModel):
    media_type: str = pydantic.Field(alias="mediaType")
    size: int
    digest: str
    platform: ManifestPlatform | None


class Manifest(pydantic.BaseModel):
    media_type: str = pydantic.Field(alias="mediaType")
    schema_version: int = pydantic.Field(alias="schemaVersion")
    layers: list[ManifestLayer] | None
    manifests: list[ImageVariantManifest] | None
    config: ManifestConfig | None
