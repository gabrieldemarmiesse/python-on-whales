from datetime import datetime
from typing import Optional

from python_on_whales.utils import DockerCamelModel


class SecretInspectResult(DockerCamelModel):
    id: Optional[str] = None
    version: Optional[dict] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    spec: Optional[dict] = None
