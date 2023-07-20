from typing import Dict, Optional

import pydantic

from python_on_whales.utils import DockerCamelModel


class ContextEndpoint(DockerCamelModel):
    host: Optional[str]
    skip_tls_verify: Optional[bool] = pydantic.Field(alias="SkipTLSVerify")


class ContextStorage(DockerCamelModel):
    metadata_path: Optional[str]
    tls_path: Optional[str] = pydantic.Field(None, alias="TLSPath")


class ContextInspectResult(DockerCamelModel):
    name: Optional[str]
    metadata: Optional[Dict[str, str]]
    endpoints: Optional[Dict[str, ContextEndpoint]]
    tls_material: Optional[dict] = pydantic.Field(None, alias="TLSMaterial")
    storage: Optional[ContextStorage]
