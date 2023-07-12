from datetime import datetime
from typing import Dict, List, Optional

from pydantic import Field

from python_on_whales.utils import DockerCamelModel, all_fields_optional


@all_fields_optional
class NodeVersion(DockerCamelModel):
    index: Optional[int]


@all_fields_optional
class NodeSpec(DockerCamelModel):
    name: Optional[str]
    labels: Optional[Dict[str, str]]
    role: Optional[str]
    availability: Optional[str]


@all_fields_optional
class NodePlatform(DockerCamelModel):
    architecture: Optional[str]
    os: Optional[str] = Field(None, alias="OS")


@all_fields_optional
class NodeNamedResourceSpec(DockerCamelModel):
    kind: Optional[str]
    value: Optional[str]


@all_fields_optional
class NodeDiscreteResourceSpec(DockerCamelModel):
    kind: Optional[str]
    value: Optional[int]


@all_fields_optional
class NodeGenericResource(DockerCamelModel):
    named_resource_spec: Optional[NodeNamedResourceSpec]
    discrete_resource_spec: Optional[NodeDiscreteResourceSpec]


@all_fields_optional
class NodeResource(DockerCamelModel):
    nano_cpus: Optional[int] = Field(None, alias="NanoCPUs")
    memory_bytes: Optional[int]
    generic_resources: Optional[List[NodeGenericResource]]


@all_fields_optional
class EnginePlugin(DockerCamelModel):
    type: Optional[str]
    name: Optional[str]


@all_fields_optional
class NodeEngine(DockerCamelModel):
    engine_version: Optional[str]
    labels: Optional[Dict[str, str]]
    plugins: Optional[List[EnginePlugin]]


@all_fields_optional
class NodeTLSInfo(DockerCamelModel):
    trust_root: Optional[str]
    cert_issuer_subject: Optional[str]
    cert_issuer_public_key: Optional[str]


@all_fields_optional
class NodeDescription(DockerCamelModel):
    hostname: Optional[str]
    platform: Optional[NodePlatform]
    resources: Optional[NodeResource]
    engine: Optional[NodeEngine]
    tls_info: Optional[NodeTLSInfo]


@all_fields_optional
class NodeStatus(DockerCamelModel):
    state: Optional[str]
    message: Optional[str]
    addr: Optional[str]


@all_fields_optional
class NodeManagerStatus(DockerCamelModel):
    leader: Optional[bool]
    reachability: Optional[str]
    addr: Optional[str]


@all_fields_optional
class NodeInspectResult(DockerCamelModel):
    id: Optional[str] = Field(None, alias="ID")
    version: Optional[NodeVersion]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    spec: Optional[NodeSpec]
    description: Optional[NodeDescription]
    status: Optional[NodeStatus]
    manager_status: Optional[NodeManagerStatus]
