from datetime import datetime
from typing import Dict, List, Optional

from pydantic import Field
from typing_extensions import Annotated

from python_on_whales.utils import DockerCamelModel


class NodeVersion(DockerCamelModel):
    index: Optional[int] = None


class NodeSpec(DockerCamelModel):
    name: Optional[str] = None
    labels: Optional[Dict[str, str]] = None
    role: Optional[str] = None
    availability: Optional[str] = None


class NodePlatform(DockerCamelModel):
    architecture: Optional[str] = None
    os: Annotated[Optional[str], Field(alias="OS")] = None


class NodeNamedResourceSpec(DockerCamelModel):
    kind: Optional[str] = None
    value: Optional[str] = None


class NodeDiscreteResourceSpec(DockerCamelModel):
    kind: Optional[str] = None
    value: Optional[int] = None


class NodeGenericResource(DockerCamelModel):
    named_resource_spec: Optional[NodeNamedResourceSpec] = None
    discrete_resource_spec: Optional[NodeDiscreteResourceSpec] = None


class NodeResource(DockerCamelModel):
    nano_cpus: Annotated[Optional[int], Field(alias="NanoCPUs")] = None
    memory_bytes: Optional[int] = None
    generic_resources: Optional[List[NodeGenericResource]] = None


class EnginePlugin(DockerCamelModel):
    type: Optional[str] = None
    name: Optional[str] = None


class NodeEngine(DockerCamelModel):
    engine_version: Optional[str] = None
    labels: Optional[Dict[str, str]] = None
    plugins: Optional[List[EnginePlugin]] = None


class NodeTLSInfo(DockerCamelModel):
    trust_root: Optional[str] = None
    cert_issuer_subject: Optional[str] = None
    cert_issuer_public_key: Optional[str] = None


class NodeDescription(DockerCamelModel):
    hostname: Optional[str] = None
    platform: Optional[NodePlatform] = None
    resources: Optional[NodeResource] = None
    engine: Optional[NodeEngine] = None
    tls_info: Optional[NodeTLSInfo] = None


class NodeStatus(DockerCamelModel):
    state: Optional[str] = None
    message: Optional[str] = None
    addr: Optional[str] = None


class NodeManagerStatus(DockerCamelModel):
    leader: Optional[bool] = None
    reachability: Optional[str] = None
    addr: Optional[str] = None


class NodeInspectResult(DockerCamelModel):
    id: Annotated[Optional[str], Field(alias="ID")] = None
    version: Optional[NodeVersion] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    spec: Optional[NodeSpec] = None
    description: Optional[NodeDescription] = None
    status: Optional[NodeStatus] = None
    manager_status: Optional[NodeManagerStatus] = None
