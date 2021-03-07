from typing import Dict

import pydantic

from python_on_whales.utils import DockerCamelModel


class ContextEndpoint(DockerCamelModel):
    host: str
    skip_tls_verify: bool = pydantic.Field(alias="SkipTLSVerify")


class ContextStorage(DockerCamelModel):
    metadata_path: str
    tls_path: str = pydantic.Field(alias="TLSPath")


class ContextInspectResult(DockerCamelModel):
    name: str
    metadata: Dict[str, str]
    endpoints: Dict[str, ContextEndpoint]
    tls_material: dict = pydantic.Field(alias="TLSMaterial")
    storage: ContextStorage
