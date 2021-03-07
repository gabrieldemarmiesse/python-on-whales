from datetime import datetime

from python_on_whales.utils import DockerCamelModel


class SecretInspectResult(DockerCamelModel):
    id: str
    version: dict
    created_at: datetime
    updated_at: datetime
    spec: dict
