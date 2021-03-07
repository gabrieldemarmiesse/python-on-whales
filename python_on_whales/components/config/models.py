class DockerObjectVersion(DockerCamelModel):
    index: int


class ConfigSpecDriver(DockerCamelModel):
    name: str
    options: Dict[str, Any]


class ConfigSpec(DockerCamelModel):
    name: str
    labels: Dict[str, str]
    data: str
    templating: Optional[ConfigSpecDriver]


class ConfigInspectResult(DockerCamelModel):
    id: str = pydantic.Field(alias="ID")
    version: DockerObjectVersion
    created_at: datetime
    updated_at: datetime
    spec: ConfigSpec
