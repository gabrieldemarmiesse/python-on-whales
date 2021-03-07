class SecretInspectResult(DockerCamelModel):
    id: str
    version: dict
    created_at: datetime
    updated_at: datetime
    spec: dict
