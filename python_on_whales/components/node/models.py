from datetime import datetime
from typing import Dict, List, Optional

from pydantic import Field

from python_on_whales.utils import DockerCamelModel


class NodeVersion(DockerCamelModel):
    index: int


class NodeSpec(DockerCamelModel):
    name: Optional[str]
    labels: Dict[str, str]
    role: str
    availability: str


class NodePlatform(DockerCamelModel):
    architecture: str
    os: str = Field(alias="OS")


class NodeNamedResourceSpec(DockerCamelModel):
    kind: str
    value: str


class NodeDiscreteResourceSpec(DockerCamelModel):
    kind: str
    value: int


class NodeGenericResource(DockerCamelModel):
    named_resource_spec: Optional[NodeNamedResourceSpec]
    discrete_resource_spec: Optional[NodeDiscreteResourceSpec]


class NodeResource(DockerCamelModel):
    nano_cpus: int = Field(alias="NanoCPUs")
    memory_bytes: int
    generic_resources: Optional[List[NodeGenericResource]]


class EnginePlugin(DockerCamelModel):
    type: str
    name: str


class NodeEngine(DockerCamelModel):
    engine_version: str
    labels: Optional[Dict[str, str]]
    plugins: List[EnginePlugin]


class NodeTLSInfo(DockerCamelModel):
    trust_root: str
    cert_issuer_subject: str
    cert_issuer_public_key: str


class NodeDescription(DockerCamelModel):
    hostname: str
    platform: NodePlatform
    resources: NodeResource
    engine: NodeEngine
    tls_info: NodeTLSInfo


class NodeStatus(DockerCamelModel):
    state: str
    message: Optional[str]
    addr: str


class NodeManagerStatus(DockerCamelModel):
    leader: bool
    reachability: str
    addr: str


class NodeInspectResult(DockerCamelModel):
    id: str = Field(alias="ID")
    version: NodeVersion
    created_at: datetime
    updated_at: datetime
    spec: NodeSpec
    description: NodeDescription
    status: NodeStatus
    manager_status: Optional[NodeManagerStatus]
