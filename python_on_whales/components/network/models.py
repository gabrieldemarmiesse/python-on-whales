from datetime import datetime
from typing import Any, Dict, List, Optional

from python_on_whales.utils import DockerCamelModel, all_fields_optional


@all_fields_optional
class NetworkIPAM(DockerCamelModel):
    driver: Optional[str]
    config: Optional[List[Dict[str, Any]]]
    options: Optional[Dict[str, Any]]


@all_fields_optional
class NetworkContainer(DockerCamelModel):
    name: Optional[str]
    endpoint_id: Optional[str]
    mac_address: Optional[str]
    ipv4_address: Optional[str]
    ipv6_address: Optional[str]


@all_fields_optional
class NetworkInspectResult(DockerCamelModel):
    name: Optional[str]
    id: Optional[str]
    created: Optional[datetime]
    scope: Optional[str]
    driver: Optional[str]
    enable_ipv6: Optional[bool]
    ipam: Optional[NetworkIPAM]
    internal: Optional[bool]
    attachable: Optional[bool]
    ingress: Optional[bool]
    containers: Optional[Dict[str, NetworkContainer]]
    options: Optional[Dict[str, Any]]
    labels: Optional[Dict[str, str]]
    config_from: Optional[dict]
    config_only: Optional[bool]
