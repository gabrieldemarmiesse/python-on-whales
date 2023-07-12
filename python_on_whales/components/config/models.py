from datetime import datetime
from typing import Any, Dict, Optional

import pydantic

from python_on_whales.utils import DockerCamelModel


class DockerObjectVersion(DockerCamelModel):
    index: Optional[int] = None


class ConfigSpecDriver(DockerCamelModel):
    name: Optional[str] = None
    options: Optional[Dict[str, Any]] = None


class ConfigSpec(DockerCamelModel):
    name: Optional[str]
    labels: Optional[Dict[str, str]]
    data: Optional[str]
    templating: Optional[ConfigSpecDriver]


class ConfigInspectResult(DockerCamelModel):
    id: Optional[str] = pydantic.Field(None, alias="ID")
    version: Optional[DockerObjectVersion]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    spec: Optional[ConfigSpec]
