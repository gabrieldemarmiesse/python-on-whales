from datetime import datetime
from typing import Dict, List, Optional

from pydantic import Field

from python_on_whales.utils import DockerCamelModel, all_fields_optional


@all_fields_optional
class NodeVersion(DockerCamelModel):
    index: int


@all_fields_optional
class NodeSpec(DockerCamelModel):
    name: Optional[str]
    labels: Dict[str, str]
    role: str
    availability: str


@all_fields_optional
class NodePlatform(DockerCamelModel):
    architecture: str
    os: str = Field(alias="OS")


@all_fields_optional
class NodeNamedResourceSpec(DockerCamelModel):
    kind: str
    value: str


@all_fields_optional
class NodeDiscreteResourceSpec(DockerCamelModel):
    kind: str
    value: int


@all_fields_optional
class NodeGenericResource(DockerCamelModel):
    named_resource_spec: Optional[NodeNamedResourceSpec]
    discrete_resource_spec: Optional[NodeDiscreteResourceSpec]


@all_fields_optional
class NodeResource(DockerCamelModel):
    nano_cpus: int = Field(alias="NanoCPUs")
    memory_bytes: int
    generic_resources: Optional[List[NodeGenericResource]]


@all_fields_optional
class EnginePlugin(DockerCamelModel):
    type: str
    name: str


@all_fields_optional
class NodeEngine(DockerCamelModel):
    engine_version: str
    labels: Optional[Dict[str, str]]
    plugins: List[EnginePlugin]


@all_fields_optional
class NodeTLSInfo(DockerCamelModel):
    trust_root: str
    cert_issuer_subject: str
    cert_issuer_public_key: str


@all_fields_optional
class NodeDescription(DockerCamelModel):
    hostname: str
    platform: NodePlatform
    resources: NodeResource
    engine: NodeEngine
    tls_info: NodeTLSInfo


@all_fields_optional
class NodeStatus(DockerCamelModel):
    state: str
    message: Optional[str]
    addr: str


@all_fields_optional
class NodeManagerStatus(DockerCamelModel):
    leader: bool
    reachability: str
    addr: str


@all_fields_optional
class NodeInspectResult(DockerCamelModel):
    id: str = Field(alias="ID")
    version: NodeVersion
    created_at: datetime
    updated_at: datetime
    spec: NodeSpec
    description: NodeDescription
    status: NodeStatus
    manager_status: Optional[NodeManagerStatus]
