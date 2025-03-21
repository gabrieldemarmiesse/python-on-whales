import datetime as dt
from typing import Any, Dict, Optional

from pydantic import Field

from python_on_whales.utils import DockerCamelModel


class SecretSpec(DockerCamelModel):
    name: str
    Labels: Dict[str, Any]


class SecretInspectResult(DockerCamelModel):
    id: Optional[str] = Field(alias="ID")
    version: Optional[dict] = None
    created_at: Optional[dt.datetime] = None
    updated_at: Optional[dt.datetime] = None
    spec: Optional[SecretSpec] = None
