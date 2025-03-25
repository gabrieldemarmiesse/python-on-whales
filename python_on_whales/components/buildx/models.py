from __future__ import annotations

import datetime as dt
from typing import Dict, List, Optional

from pydantic import Field
from typing_extensions import Annotated

from python_on_whales.utils import DockerCamelModel


class BuilderNode(DockerCamelModel):
    name: Optional[str] = None
    endpoint: Optional[str] = None
    flags: Optional[List[str]] = None
    status: Optional[str] = None
    version: Optional[str] = None
    ids: Annotated[Optional[List[str]], Field(alias="IDs")] = None
    platforms: Optional[List[str]] = None
    labels: Optional[Dict[str, str]] = None


class BuilderInspectResult(DockerCamelModel):
    name: Optional[str] = None
    driver: Optional[str] = None
    last_activity: Optional[dt.datetime] = None
    dynamic: Optional[bool] = None
    nodes: Optional[List[BuilderNode]] = None
