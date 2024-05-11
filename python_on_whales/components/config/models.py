import sys
from datetime import datetime
from typing import Any, Dict, Optional

import pydantic

from python_on_whales.utils import DockerCamelModel

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated


class DockerObjectVersion(DockerCamelModel):
    index: Optional[int] = None


class ConfigSpecDriver(DockerCamelModel):
    name: Optional[str] = None
    options: Optional[Dict[str, Any]] = None


class ConfigSpec(DockerCamelModel):
    name: Optional[str] = None
    labels: Optional[Dict[str, str]] = None
    data: Optional[str] = None
    templating: Optional[ConfigSpecDriver] = None


class ConfigInspectResult(DockerCamelModel):
    id: Annotated[Optional[str], pydantic.Field(alias="ID")] = None
    version: Optional[DockerObjectVersion] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    spec: Optional[ConfigSpec] = None
