from typing import Dict, Optional

import pydantic
from typing_extensions import Annotated

from python_on_whales.utils import DockerCamelModel


class ContextEndpoint(DockerCamelModel):
    host: Optional[str] = None
    skip_tls_verify: Annotated[
        Optional[bool], pydantic.Field(alias="SkipTLSVerify")
    ] = None


class ContextStorage(DockerCamelModel):
    metadata_path: Optional[str] = None
    tls_path: Annotated[Optional[str], pydantic.Field(alias="TLSPath")] = None


class ContextInspectResult(DockerCamelModel):
    name: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None
    endpoints: Optional[Dict[str, ContextEndpoint]] = None
    tls_material: Annotated[Optional[dict], pydantic.Field(alias="TLSMaterial")] = None
    storage: Optional[ContextStorage] = None
