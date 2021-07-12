from datetime import datetime

from python_on_whales.utils import DockerCamelModel, all_fields_optional


@all_fields_optional
class SecretInspectResult(DockerCamelModel):
    id: str
    version: dict
    created_at: datetime
    updated_at: datetime
    spec: dict
