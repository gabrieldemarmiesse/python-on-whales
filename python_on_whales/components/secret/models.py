from datetime import datetime
from typing import Optional

from python_on_whales.utils import DockerCamelModel, all_fields_optional


@all_fields_optional
class SecretInspectResult(DockerCamelModel):
    id: Optional[str]
    version: Optional[dict]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    spec: Optional[dict]
