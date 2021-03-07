from datetime import datetime

from docker_cli_wrapper.utils import DockerCamelModel


class SecretInspectResult(DockerCamelModel):
    id: str
    version: dict
    created_at: datetime
    updated_at: datetime
    spec: dict
